# Bulanik Mantik Dersi Donem Projesi

## Proje konusu

Bu proje, banka kredi basvurularinda risk skorunu tahmin eden bir Mamdani tipi
bulanik kontrolcu uygular. Sistem, kesin sinirlarla karar vermenin zor oldugu
kredi risk degerlendirme probleminde uc girisi birlikte yorumlar:

- Aylik gelir (0-100 bin TL)
- Kredi notu (0-1000 puan)
- Borc/Gelir orani (0-100%)

Cikti degiskeni 0-100 araliginda kredi risk skorudur. Skor yukseldikce kredi
basvurusunun riskli olma ihtimali artar.

## Kullanilan teknolojiler

- Python
- scikit-fuzzy
- NumPy
- Matplotlib
- Flask

Not: Kod, `scikit-fuzzy` import edilebilen ortamlarda bu paketi kullanir.
32-bit Windows gibi SciPy kurulumu sorunlu ortamlarda ayni trimf, trapmf,
uyelik enterpolasyonu ve centroid islemleri NumPy tabanli yedek katmanla
calisir.

## Kurulum

```bash
python -m pip install -r requirements.txt
```

## Calistirma

```bash
python app.py
```

Tarayicida `http://127.0.0.1:5000` adresini acarak arayuzu kullanabilirsiniz.
Giris degerleri slider veya metin kutusu ile degistirilebilir. Sonuc alaninda
centroid durulastirma grafigi, aktif kurallar ve sayisal risk skoru guncellenir.

## Dosyalar

- `app.py`: Flask arayuzu.
- `fuzzy_credit_risk.py`: Uyelik fonksiyonlari, 27 kural, Mamdani cikarim ve centroid durulastirma.
- `test_scenarios.py`: Ornek senaryolari konsolda tablo olarak uretir.
- `RAPOR.md`: Proje raporu.
- `requirements.txt`: Proje bagimliliklari.

## Test senaryolari

```bash
python test_scenarios.py
```

Bu komut guclu profil, dengeli profil, borc yuku fazla profil ve riskli basvuru
gibi farkli durumlar icin risk skorlarini hesaplar.
