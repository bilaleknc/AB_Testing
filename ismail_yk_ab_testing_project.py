#                 -------------------------------------------------------------------
# ----------------  AB Testi ile Bidding Yöntemlerinin Dönüşümünün Karşılaştırılması  ----------------
#                 -------------------------------------------------------------------




##########################################
## İş Problemi
##########################################



"""
Facebook kısa süre önce mevcut "maximum bidding" adı verilen teklif verme türüne alternatif olarak yeni bir teklif türü
olan "average bidding"’i tanıttı.

Müşterilerimizden biri olan bombabomba.com, bu yeni özelliği test etmeye karar verdi ve average bidding'in maximum
bidding'den daha fazla dönüşüm getirip getirmediğini anlamak için bir A/B testi yapmak istiyor.

A/B testi 1 aydır devam ediyor ve bombabomba.com şimdi sizden bu A/B testinin sonuçlarını analiz etmenizi bekliyor.
Bombabomba.com için nihai başarı ölçütü Purchase'dır. Bu
nedenle, istatistiksel testler için Purchase metriğine odaklanılmalıdır.

"""



###########################################
## Veri Seti Hikayesi
###########################################



"""
Bir firmanın web site bilgilerini içeren bu veri setinde kullanıcıların gördükleri ve tıkladıkları reklam sayıları gibi 
bilgilerin yanı sıra buradan gelen kazanç bilgileri yer almaktadır. Kontrol ve Test grubu olmak üzere iki ayrı veri seti vardır. 
Bu veri setleri ab_testing.xlsx excel’inin ayrı sayfalarında yer almaktadır. Kontrol grubuna Maximum Bidding, test grubuna 
Average Bidding uygulanmıştır.
"""

"""
 	4 Değişken			40 Gözlem			26 KB	

Impression	    Reklam görüntüleme sayısı
Click	        Görüntülenen reklama tıklama sayısı
Purchase	    Tıklanan reklamlar sonrası satın alınan ürün sayısı
Earning	        Satın alınan ürünler sonrası elde edilen kazanç
"""





########################################################################################################################
#                                                  Let's get it started
########################################################################################################################



# Gerekli kütüphaneler yüklensin, ayarlamalar yapılsın ve verimiz okunsun...


import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import shapiro, levene, ttest_ind, mannwhitneyu


pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', 10)
pd.set_option('display.float_format', lambda x: '%.5f' % x)


df_control = pd.read_excel("C:/Users/Victus/Desktop/VBO/projeler/AB_testing/ab_testing.xlsx", sheet_name="Control Group")
df_test = pd.read_excel("C:/Users/Victus/Desktop/VBO/projeler/AB_testing/ab_testing.xlsx", sheet_name="Test Group")


# Verimizi kontrol etmek adına bir fonksiyon tanımlayalım...

def check_df(dataframe, head=5, tail=5):
    print("##################### Shape #####################")
    print(dataframe.shape)

    print("##################### Types #####################")
    print(dataframe.dtypes)

    print("##################### Head #####################")
    print(dataframe.head(head))

    print("##################### Tail #####################")
    print(dataframe.tail(tail))

    print("##################### NA #####################")
    print(dataframe.isnull().sum())

    print("##################### Descriptive Statistic #####################")
    print(dataframe.describe().T)


check_df(df_control)
check_df(df_test)



# Verimiz gayet sağlıklı gözükmekte fakat yine de sizinle outlier olan bir veri bulunup bulunmadığını
# test eden güzel fonksiyonlar tanımlayalım...

def outlier_thresholds(dataframe, col_name, q1=0.25, q3=0.75):
    quartile1 = dataframe[col_name].quantile(q1)
    quartile3 = dataframe[col_name].quantile(q3)
    interquantile_range = quartile3 - quartile1
    up_limit = quartile3 + 1.5 * interquantile_range
    low_limit = quartile1 - 1.5 * interquantile_range
    return low_limit, up_limit

def check_outlier(dataframe, col_name):
    low_limit, up_limit = outlier_thresholds(dataframe, col_name)
    if dataframe[(dataframe[col_name] > up_limit) | (dataframe[col_name] < low_limit)].any(axis=None):
        return True
    else:
        return False


check_outlier(df_control, "Purchase")
check_outlier(df_test, "Purchase")

# Görüldüğü üzere Purchase değişkeninde outlier veri bulamadık aynı şekilde diğer değişkenlerde de bulunmamaktadır.
# Görsel olarak da gözlemledikten sonra bir sonraki aşamamıza geçebiliriz.

sns.boxplot(x=df_control["Purchase"])
plt.show()
sns.boxplot(x=df_test["Purchase"])
plt.show()



#####################################################################
# Verimize ilk bakışımızı attığımıza göre A/B testinge başlayabiliriz.
#####################################################################


############################
# 1. Hipotezi Kuralım
############################


# H0: M1 = M2
""" 
Maximum bidding stratejisi uygulananlar ile average bidding stratejisi uygulananların satım alım sayısında istatistiksel
olarak anlamlı bir fark yoktur.
"""

# H1: M1 != M2
""" 
Maximum bidding stratejisi uygulananlar ile average bidding stratejisi uygulananların satım alım sayısında istatistiksel
olarak anlamlı bir fark vardır.
"""

# Kontrol ve test grubu için purchase (kazanç) ortalamalarını analiz edelim.
df_test.Purchase.mean()
df_control.Purchase.mean()

# Hipotez testi yapılmadan önce varsayım kontrollerini yapalım...
# Bunlar Normallik Varsayımı ve Varyans Homojenliğidir. Kontrol ve test grubunun normallik varsayımına uyup uymadığını
# Purchase değişkeni üzerinden ayrı ayrı test edelim.

"""
Normallik Varsayımı :
H0: Normal dağılım varsayımı sağlanmaktadır. 
H1: Normal dağılım varsayımı sağlanmamaktadır. 
"""

test_stat, pvalue = shapiro(df_test["Purchase"])
print('Test Stat = %.4f, p-value = %.4f' % (test_stat, pvalue))

test_stat, pvalue = shapiro(df_control["Purchase"])
print('Test Stat = %.4f, p-value = %.4f' % (test_stat, pvalue))

""""
pvalue değerleri 0.05 den küçük olduğu için H0 reddedilir ve normallik varsayımı olmadığı kabul edilir.Bu durumda 
varyans homejenliği testi yapmaya gerek kalmaksızın non-parametrik test olan mannwhitneyu yapılabilir
"""

# Hipotezi uygulamak adına mannwhitneyu testini kullanalım


test_stat, pvalue = mannwhitneyu(df_test["Purchase"], df_control["Purchase"])
print('Test Stat = %.4f, p-value = %.4f' % (test_stat, pvalue))

"""
Mannwhitneyu testimiz sonucunda pvalue değeri 0.05 üstünde çıkmış ve bu sebeple H0 reddedilememiştir. Sözün özü 
test ve kontrol grubunda istatistiksel olarak anlamlı bir fark bulunamamıştır. 
"""





