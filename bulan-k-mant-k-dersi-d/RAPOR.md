# Bulanik Mantik ile Banka Kredi Risk Degerlendirme Sistemi

## 1. Giris ve problem tanimi

Banka kredi basvurularinda karar verme sureci yalnizca tek bir sayisal degere
bagli degildir. Gelir seviyesi, kredi notu ve mevcut borc yuku birlikte
degerlendirilir. Bu degiskenlerin sinirlari keskin olmadigi icin klasik
mantikla "uygun/uygun degil" seklinde karar vermek gercek hayati tam temsil
etmez. Ornegin 649 kredi notu ile 650 kredi notu arasinda cok buyuk bir fark
yoktur, ancak keskin esik kullanan sistemlerde farkli kararlar cikabilir.

Bu proje, kredi riskini 0-100 araliginda hesaplayan Mamdani tipi bir bulanik
kontrolcu tasarlar. Amac, belirsizlik iceren finansal karar surecini dilsel
degiskenler ve uzman kurallari ile modellemektir.

## 2. Bulanik mantigin uygunlugu

Kredi risk degerlendirme problemi bulanik mantiga uygundur cunku:

- Girdi degiskenleri dogal olarak "dusuk", "orta", "yuksek" gibi dilsel
  ifadelerle yorumlanir.
- Degiskenler arasinda kesin ve tek dogru iliski yoktur.
- Bir basvuru ayni anda birden fazla kumeye belirli derecelerde ait olabilir.
- Uzman gorusu IF-THEN kurallari ile anlasilir bicimde modellenebilir.

## 3. Sistem tasarimi

### 3.1 Giris ve cikis degiskenleri

| Degisken | Tur | Aralik | Dilsel tanimlar |
|---|---:|---:|---|
| Aylik gelir | Giris | 0-100 bin TL | dusuk, orta, yuksek |
| Kredi notu | Giris | 0-1000 puan | dusuk, orta, yuksek |
| Borc/Gelir orani | Giris | 0-100% | dusuk, orta, yuksek |
| Kredi risk skoru | Cikis | 0-100 puan | dusuk, orta, yuksek |

### 3.2 Uyelik fonksiyonlari

Projede ucgen ve yamuk uyelik fonksiyonlari kullanilmistir:

- Gelir dusuk: trapmf `[0, 0, 15, 35]`
- Gelir orta: trimf `[25, 50, 75]`
- Gelir yuksek: trapmf `[65, 85, 100, 100]`
- Kredi notu dusuk: trapmf `[0, 0, 350, 550]`
- Kredi notu orta: trimf `[450, 650, 800]`
- Kredi notu yuksek: trapmf `[700, 850, 1000, 1000]`
- Borc/Gelir dusuk: trapmf `[0, 0, 20, 35]`
- Borc/Gelir orta: trimf `[25, 45, 65]`
- Borc/Gelir yuksek: trapmf `[55, 75, 100, 100]`
- Risk dusuk: trapmf `[0, 0, 20, 40]`
- Risk orta: trimf `[30, 50, 70]`
- Risk yuksek: trapmf `[60, 80, 100, 100]`

### 3.3 Kural tabani

Sistemde 3 giris degiskeninin tum dilsel kombinasyonlarini kapsayan 27 IF-THEN
kurali bulunur. Ornek kurallar:

- IF gelir dusuk AND kredi notu dusuk AND borc/gelir orani yuksek THEN risk yuksek
- IF gelir orta AND kredi notu yuksek AND borc/gelir orani orta THEN risk dusuk
- IF gelir yuksek AND kredi notu yuksek AND borc/gelir orani yuksek THEN risk orta
- IF gelir dusuk AND kredi notu yuksek AND borc/gelir orani dusuk THEN risk dusuk

Tum kural listesi Streamlit arayuzundeki "Kural tabani" sekmesinde tablo olarak
gosterilir.

### 3.4 Cikarim motoru

Mamdani cikarim yontemi kullanilmistir.

- AND islemi icin minimum operatoru kullanilir.
- Her kuralin aktivasyon degeri, ilgili uc giris uyelik derecesinin minimumudur.
- Kural ciktilari ilgili risk uyelik fonksiyonu uzerinden kesilir.
- Birden fazla kuralin ciktilari maksimum operatoru ile birlestirilir.

### 3.5 Durulastirma

Bulanik cikti, agirlik merkezi yani centroid metodu ile tek bir sayisal risk
skoruna donusturulur. Hesaplanan skor 0'a yaklastikca dusuk risk, 100'e
yaklastikca yuksek risk anlamina gelir.

## 4. Python uygulamasi

Uygulama Flask arayuzu ile gelistirilmistir. Arayuzde:

- Giris degerleri slider ile degistirilir.
- Hesapla butonu ile sonuc yeniden uretilir.
- Uyelik fonksiyonlari grafik uzerinde gosterilir.
- Aktif kurallar aktivasyon derecesine gore listelenir.
- Durulastirma sonucu sayisal ve grafiksel olarak sunulur.
- Test senaryolari tablo ve grafik halinde incelenir.

## 5. Test sonuclari ve analiz

`python test_scenarios.py` komutu ile farkli profiller test edilmistir.

| Senaryo | Aylik Gelir | Kredi Notu | Borc/Gelir | Risk Skoru | Baskin Cikti |
|---|---:|---:|---:|---:|---|
| Guclu profil | 85 | 880 | 18 | 15.55 | dusuk |
| Dengeli profil | 52 | 650 | 42 | 50.00 | orta |
| Gelir dusuk, not iyi | 24 | 790 | 32 | 37.88 | orta |
| Borc yuku fazla | 70 | 720 | 78 | 50.00 | orta |
| Riskli basvuru | 18 | 390 | 82 | 83.67 | yuksek |

Sonuclarin yorumu:

- Geliri yuksek, kredi notu yuksek ve borc orani dusuk basvuru dusuk risk uretir.
- Geliri orta, notu orta ve borc orani orta profil orta risk uretir.
- Borc/Gelir orani cok yuksek oldugunda risk skoru artar.
- Gelir ve kredi notu dusukken risk yuksek seviyeye cikar.

Bu sonuclar, kural tabaninin uzman sezgisine uygun calistigini gosterir.

## 6. Guclu ve zayif yonler

Guclu yonler:

- Karar mantigi seffaf ve aciklanabilirdir.
- Keskin esikler yerine kademeli gecisler kullanir.
- Kural tabani kolayca genisletilebilir.
- Arayuz, aktif kurallari ve uyelik fonksiyonlarini gorsellestirir.

Zayif yonler:

- Kural tabani uzman gorusune baglidir.
- Gercek banka verisi ile egitilmis bir model degildir.
- Uyelik fonksiyonu parametreleri elle belirlenmistir.
- Degisken sayisi arttikca kural sayisi hizla artar.

## 7. Guncel yaklasimlarla karsilastirma

Guncel finansal risk sistemlerinde lojistik regresyon, karar agaclari, rassal
orman, gradient boosting ve derin ogrenme gibi veri odakli yontemler sik
kullanilir. Bu yontemler buyuk veri setlerinde yuksek dogruluk saglayabilir.
Ancak aciklanabilirlikleri her zaman kolay degildir. Bulanik mantik ise
ozellikle ders projesi ve karar aciklama senaryolarinda avantajlidir; cunku
hangi kuralin ne kadar aktif oldugu dogrudan gorulebilir.

## 8. Sonuc

Bu projede kredi risk degerlendirme problemi icin uc girisli bir bulanik
kontrolcu tasarlanmistir. Uygulama, uyelik fonksiyonlari, bulaniklastirma,
Mamdani cikarim mekanizmasi, kural aktivasyonlari ve centroid durulastirma
adimlarini kapsamaktadir. Streamlit arayuzu sayesinde kullanici girisleri
anlik degistirilebilir ve sonuc grafiksel olarak incelenebilir.

## 9. Kaynakca

- Zadeh, L. A. (1965). Fuzzy Sets. Information and Control.
- Ross, T. J. (2010). Fuzzy Logic with Engineering Applications.
- scikit-fuzzy dokumantasyonu: https://pythonhosted.org/scikit-fuzzy/
- Flask dokumantasyonu: https://flask.palletsprojects.com/
