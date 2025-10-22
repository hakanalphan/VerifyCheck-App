

# 🧠 VerifyCheck – FastAPI + EasyOCR 

Kimlik (ön yüz) ve **imzalı başvuru formu** görsellerinden **Ad Soyad** ve **T.C. Kimlik Numarası (TCKN)** bilgilerini OCR ile çıkarıp **tutarlılığını denetleyen** bir PoC (Proof of Concept) projesidir.

---

## 🚀 Hızlı Başlangıç (Docker ile Çalıştır)

```bash
# 1. Depoyu klonla
git clone https://github.com/hakanalphan/VerifyCheck-App.git verifycheck
cd verifycheck

# 2. Docker ile çalıştır
docker compose up --build

# veya
docker build -t verifycheck .
docker run --rm -p 8000:8000 verifycheck

# 3. Tarayıcıda aç
http://127.0.0.1:8000
```

---

## 💡 Projenin Amacı

Bu proje, KYC (Know Your Customer) süreçlerinde belge doğrulama işlemini otomatikleştirmek için geliştirilmiştir.
Kullanıcı iki belge (kimlik ve form) yükler → sistem OCR ile verileri okur → isim ve TCKN eşleşmesini kontrol eder → sonucu **JSON veya arayüzde renkli mesaj** olarak gösterir.


---

## 🗂️ Klasörleme

| Klasör       | Açıklama                                |
| ------------ | --------------------------------------- |
| `config/`    | Pydantic settings (env tabanlı ayarlar) |
| `core/`      | Request/response modelleri              |
| `services/`  | EasyOCR motoru ve eşleştirme servisi    |
| `utils/`     | TCKN validasyonu, metin normalizasyonu  |
| `api/`       | FastAPI router’ları                     |
| `templates/` | index.html (UI)                         |
| `static/`    | CSS vb. statik dosyalar                 |
| `main.py`    | FastAPI uygulama montajı                |

---

## ⚙️ Geliştirici Modunda Çalıştırma

```bash
pip install -r requirements.txt
uvicorn main:app --reload
# http://127.0.0.1:8000
```

---

## 🌍 Ortam Değişkenleri

| Değişken                  | Tip   | Varsayılan | Açıklama                     |
| ------------------------- | ----- | ---------- | ---------------------------- |
| `KYC_MIN_NAME_SIMILARITY` | int   | 80         | Ad-Soyad benzerlik eşiği     |
| `KYC_MIN_OCR_CONFIDENCE`  | float | 0.35       | OCR güven eşiği              |
| `KYC_MAX_UPLOAD_MB`       | int   | 10         | Maksimum yükleme boyutu (MB) |

---

## 🧩 İş Akışı

1. Kullanıcı **kimlik ve form** görsellerini yükler.
2. **EasyOCR** görsellerden metni çıkarır.
3. Metinler normalize edilir (Unicode, Türkçe karakter, büyük harf).
4. Regex ve algoritmik kontroller ile:

   * **Ad Soyad** bulunur
   * **TCKN** çıkarılır ve mod-11 doğrulaması yapılır
5. Sistem, benzerlik ve doğruluk skorlarını hesaplar.
6. Sonuçlar:

   * **UI:** yeşil (başarılı) veya kırmızı (hata) kutu
   * **API:** JSON çıktı

---

##  TCKN Doğrulama

* 11 haneli olmalı, ilk hane `0` olamaz.
* 10. hane: tek/çift toplamına göre mod-10
* 11. hane: ilk 10 hanenin toplamının mod-10’u

Hatalıysa `tckn_match = false` döner ve doğrulama başarısız olur.

---

##  Hata / Başarı Görünümü

* **Hata:** Kırmızı kutu (örnek: TCKN uyuşmuyor)
* **Başarı:** Yeşil kutu + JSON sonuç

---

##  Güvenlik

* Yüklenen dosyalar **geçici dizinde** tutulur, işlem sonunda **otomatik silinir**.
* TCKN, isim gibi kişisel veriler loglarda **maskelenmezse** üretimde dikkat edilmelidir.
* `KYC_MAX_UPLOAD_MB` sınırıyla **dosya boyutu** kontrolü sağlanır.

---

##  Notlar

* EasyOCR **CPU modda** çalışır. GPU desteği için Torch + CUDA gerekir.
* Türkçe metinlerde **diakritik ve büyük harf normalizasyonu** aktiftir.
* Docker imajı üretim ortamında kolayca ölçeklenebilir.

---

##  Geliştirme Yol Haritası

* [ ] Llama Vision OCR entegrasyonu (kimlik ve form alanları için)
* [ ] DeepSeek-OCR entegrasyonu (karmaşık dokümanlar için)
* [ ] RabbitMQ/Kafka kuyruğu ile toplu OCR işleme
* [ ] Gelişmiş isim benzerlik algoritması (fuzzy matching)

---

 **Özet:**
VerifyCheck, OCR tabanlı kimlik doğrulama için geliştirilen bir PoC’tir.
EasyOCR ile kimlik ve form verilerini okur, TCKN ve isim uyumunu denetler.
**Docker veya FastAPI** üzerinden kolayca çalıştırılabilir.

---



