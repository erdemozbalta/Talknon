# Talknon

<p align="center">
  <a href="./README_TR.md"><img src="https://img.shields.io/badge/Language-Türkçe-E31E24?style=for-the-badge" alt="Türkçe" /></a>
  <a href="./README.md"><img src="https://img.shields.io/badge/Language-English-00247D?style=for-the-badge" alt="English" /></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white" alt="Flask" />
  <img src="https://img.shields.io/badge/Socket.io-010101?style=for-the-badge&logo=socketdotio&logoColor=white" alt="Socket.io" />
  <img src="https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white" alt="MySQL" />
  <img src="https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white" alt="HTML5" />
  <img src="https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white" alt="CSS3" />
  <img src="https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black" alt="JavaScript" />
  <img src="https://img.shields.io/badge/SQLAlchemy-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white" alt="SQLAlchemy" />
</p>

Talknon, kafelere gelen müşterilerin fiziksel olarak aynı mekandayken masa QR kodları ve GPS geofence doğrulaması ile anlık olarak sohbet etmesini, anonim profillerle eşleşmesini (Match) ve birebir güvenli mesajlaşmasını sağlayan lokasyon bazlı gerçek zamanlı bir sosyal etkileşim platformudur.

---

## İçindekiler

- [Proje Hakkında](#proje-hakkında)
- [Problem ve Motivasyon](#problem-ve-motivasyon)
- [Hedef Kitle](#hedef-kitle)
- [Özellikler](#özellikler)
- [Uygulama Akışı](#uygulama-akışı)
- [Ekran Görüntüleri](#ekran-görüntüleri)
- [Teknoloji Yığını](#teknoloji-yığını)
- [Mimari Yapı](#mimari-yapı)
- [Veritabanı Yapısı](#veritabanı-yapısı)
- [WebSocket ve API Mimarisi](#websocket-ve-api-mimarisi)
- [Kurulum ve Çalıştırma](#kurulum-ve-çalıştırma)
- [Proje Yapısı](#proje-yapısı)
- [Güvenlik ve Moderasyon](#güvenlik-ve-moderasyon)

---

## Proje Hakkında

Talknon, geleneksel kafe deneyimini dijital sosyal etkileşimle birleştiren tam yığın (full-stack) bir web uygulamasıdır. Sistem üç temel kullanıcı rolünü tek bir altyapı üzerinde koordine eder:

- **Müşteri (Kullanıcı):** Masa QR kodunu okutup konum doğrulamasıyla kafe odasına katılır, kafedeki diğer müşterilerle anonim rumuzla genel sohbet eder, profilleri inceleyip karşılıklı eşleşme (match) isteği gönderir ve özel sohbete (DM) geçer.
- **Kafe İşletmesi:** Kendisine tahsis edilen özel giriş koduyla yönetim paneline erişir, odadaki canlı sohbeti izler, kural ihlali yapan kullanıcıları kafeden yasaklar, mesajları susturur ve müşteri şikayetlerini yönetir.
- **Sistem Yöneticisi (Admin):** Platform geneline yeni kafe tanımlar, coğrafi koordinat ve yarıçap belirler, dinamik QR kodları oluşturur, tüm kullanıcıları görüntüler ve sistem çapında güvenlik/ceza kurallarını uygular.

Uygulamanın sunucu tarafı Python/Flask mimarisiyle geliştirilmiş olup gerçek zamanlı çift yönlü iletişim için Flask-SocketIO ve Eventlet kullanılmıştır. Veritabanı katmanında MySQL ve SQLAlchemy ORM yer alır. Ön yüz ise saf HTML5, CSS3 (Mobile-First responsive dark tema) ve Vanilla JavaScript ile herhangi bir harici ağır kütüphaneye ihtiyaç duymadan ultra hızlı çalışacak şekilde tasarlanmıştır.

---

## Problem ve Motivasyon

Sosyal ortamlarda (özellikle kafe ve lounge mekanlarında) insanlar birbirleriyle iletişim kurmak, yeni insanlarla tanışmak istemekte ancak ilk adımı atma çekingenliği, gizlilik kaygıları ve fiziksel engeller nedeniyle bu etkileşim çoğunlukla gerçekleşememektedir.

Öte yandan mevcut arkadaşlık veya mesajlaşma uygulamaları:
- Fiziksel mekanla gerçek bir bağ kurmaz (aynı kafede oturup oturmadığınızı bilmez).
- Konum doğrulaması olmadan binlerce kilometre uzaktaki insanları listeler.
- Anonimliği ve anlık mekan içi güvenliği koruyacak yerel işletme moderasyonuna sahip değildir.

**Talknon bu boşluğu kapatmak için tasarlanmıştır:**

- **Masa QR Kodu & GPS Geofence:** Yalnızca fiziken kafede bulunan müşteriler odaya erişebilir; konum hilesi yapanlar sisteme dahil edilmez.
- **Tam Gizlilik ve Anonimlik:** Kullanıcılar gerçek isimlerini veya telefon numaralarını paylaşmak zorunda kalmadan kafeye özel anonim rumuzlarla sosyalleşir.
- **Çift Taraflı Eşleşme Onayı:** Birebir özel mesajlaşma (DM) ancak her iki taraf da eşleşmeyi onayladığında başlar; istenmeyen rahatsızlıkların önüne geçilir.
- **Kafe Odaklı Moderasyon:** İşletme sahipleri kendi mekanlarındaki sohbet kalitesini ve müşteri huzurunu korumak için doğrudan canlı müdahale yetkisine sahiptir.

---

## Hedef Kitle

| Segment | Problem | Çözüm |
|---------|---------|-------|
| **Kafe Müşterileri** | Aynı mekandaki insanlarla tanışma çekingenliği ve gizlilik endişesi | QR kod ve GPS ile anonim kafe odasına katılıp güvenle sohbet ve eşleşme |
| **Kafe İşletmecileri** | Mekanda müşteri etkileşimini artırma ve müşteri bağlılığı sağlama ihtiyacı | Özel işletme paneli, canlı sohbet monitörü, kafe bazlı istatistikler |
| **Platform Yöneticisi** | Çoklu mekanların ve sistem güvenliğinin merkezi denetimi | Kafe tanımlama, harita üzerinden geofence belirleme, QR üretimi, global ban sistemi |

---

## Özellikler

### Müşteri (Kullanıcı) Modülü

- **QR Kod ile Odaya Katılma:** Masadaki QR kodu kamerayla okutarak anında ilgili kafenin lobisine yönlendirilme.
- **GPS Konum Doğrulaması:** Haversine formülü ile kullanıcının kafe yarıçapı (örneğin 25-100 metre) içinde olup olmadığını gerçek zamanlı doğrulama.
- **Anonim Rumuz (Nickname) Sistemi:** Kullanıcı kafeye girerken o mekana özel bir rumuz belirler; telefon numarası veya kimlik bilgisi gizli kalır.
- **Canlı Kafe Sohbeti:** WebSockets üzerinden sıfır gecikmeyle toplu kafe içi mesajlaşma, aktif kullanıcı listesi ve rumuz renklendirmesi.
- **Eşleşme (Match) Mekanizması:** Sohbet listesindeki kullanıcıların profillerini inceleme, eşleşme isteği gönderme ve kabul etme.
- **Birebir Özel Mesajlaşma (DM):** Kabul edilen eşleşmeler arasında anlık, şifreli ve iki yönlü özel sohbet akışı.
- **Eşleşmeyi Kaldırma (Unmatch):** Taraflardan biri eşleşmeyi kaldırdığında her iki tarafta da sohbetin ve kartların sayfa yenilenmeden anlık silinmesi.
- **Kullanıcı Engelleme ve Şikayet:** İstenmeyen kullanıcıları engelleme, kural dışı mesajları sebep belirterek işletmeye/admine raporlama.
- **Profil & Ayarlar:** Avatar yükleme, şifre değiştirme, engellenenler listesini yönetme ve dil tercihi (Türkçe/İngilizce).

### Kafe İşletmesi Modülü

- **Özel İşletme Girişi:** Kafeye özel kod (`TLK-XXXXXX`) ve şifre ile güvenli işletme paneline giriş.
- **Canlı Sohbet Monitörü:** Kafede dönen mesajları ve odadaki aktif kullanıcı sayısını anlık takip etme.
- **Kafeden Yasaklama (Ban):** Kural ihlali yapan kullanıcıyı kafeden belirli süre veya kalıcı olarak men etme.
- **Mesaj Susturma:** Çok hızlı veya uygunsuz yazan kullanıcılara geçici sohbet kısıtlaması uygulama.
- **Rapor ve Şikayet İnceleme:** Müşterilerden gelen mesaj şikayetlerini gerekçeleriyle birlikte inceleyip aksiyon alma.
- **İşletme İstatistikleri:** Toplam oturum, anlık aktif müşteri, toplam mesaj ve eşleşme sayılarını izleme.

### Yönetici (Admin) Modülü

- **Kafe Yönetimi:** Yeni kafe ekleme, harita üzerinden enlem/boylam koordinatlarını belirleme, geofence yarıçapı atama.
- **Dinamik QR Kod Üretimi:** Kafe oluşturulduğunda yüksek çözünürlüklü fiziki baskıya hazır masa QR kodlarının otomatik üretilmesi.
- **Kullanıcı Denetimi:** Tüm kayıtlı kullanıcıları listeleme, hesap detaylarını inceleme, global sistem yasağı koyma veya hesap silme.
- **Güvenlik Merkezi:** Platform genelindeki şikayetleri, aktif banları ve ihlalleri merkezi olarak görüntüleme.
- **Platform Analitiği:** Sistem geneli toplam kullanıcı, aktif kafe, günlük mesaj ve oturum hacmini takip etme.

---

## Uygulama Akışı

Uygulamanın uçtan uca yaşam döngüsü aşağıdaki aşamalardan oluşur:

```
Aşama 1 — Platform Hazırlığı (Admin)
1. Admin        → Yönetici paneline giriş yapar.
2. Admin        → Yeni kafe tanımlar (İsim, harita koordinatları, kapsama yarıçapı).
3. Admin        → Sistem kafe için benzersiz işletme kodunu ve masa QR kodunu otomatik üretir.
4. Admin        → Kafe işletmecisine giriş bilgilerini teslim eder.

Aşama 2 — Kafeye Giriş ve Doğrulama (Müşteri)
1. Müşteri      → Kafedeki masada bulunan QR kodu telefonuyla okutur.
2. Sistem       → Tarayıcıdan GPS konum izni ister ve Haversine formülü ile mesafeyi ölçer.
3. Müşteri      → Konum geçerliyse kafe lobisine yönlendirilir, anonim rumuzunu seçer.
4. Müşteri      → Kafe ortak sohbet odasına bağlanır.

Aşama 3 — Kafe İçi Sohbet ve Eşleşme (Müşteri)
1. Müşteri      → Canlı odada diğer müşterilerle mesajlaşır.
2. Müşteri      → Odadaki bir kullanıcının kartına tıklayıp eşleşme isteği gönderir.
3. Karşı Taraf  → Bildirimi anlık olarak alır; onaylarsa özel sohbet (DM) açılır.
4. Taraflar     → Birebir gizli sohbete başlar. İstedikleri an eşleşmeyi sonlandırabilirler.

Aşama 4 — İşletme Denetimi ve Moderasyon (Kafe & Admin)
1. İşletme      → Kendi paneline girerek canlı mesaj akışını izler.
2. Müşteri      → Uygunsuz bir mesajı işletmeye şikayet eder.
3. İşletme      → İhlalciyi kafeden men eder veya mesaj yazmasını susturur.
4. Admin        → Ciddi ihlallerde kullanıcıyı platform genelinde kalıcı olarak banlar.
```

---

## Ekran Görüntüleri

### Müşteri (Kullanıcı) Ekranları

<table>
  <tr>
    <td align="center"><img src="docs/screenshots/user/login.png" width="220"/><br/><sub><b>Kullanıcı Girişi</b></sub></td>
    <td align="center"><img src="docs/screenshots/user/qr_scan_entry.png" width="220"/><br/><sub><b>QR Kod Girişi</b></sub></td>
    <td align="center"><img src="docs/screenshots/user/live_chat.png" width="220"/><br/><sub><b>Canlı Kafe Sohbeti</b></sub></td>
    <td align="center"><img src="docs/screenshots/user/match_success.png" width="220"/><br/><sub><b>Eşleşme Bildirimi</b></sub></td>
  </tr>
  <tr>
    <td align="center"><img src="docs/screenshots/user/dm_chat.png" width="220"/><br/><sub><b>Birebir Özel DM</b></sub></td>
    <td align="center"><img src="docs/screenshots/user/dm_match_requests.png" width="220"/><br/><sub><b>Eşleşme İstekleri</b></sub></td>
    <td align="center"><img src="docs/screenshots/user/unmatch.png" width="220"/><br/><sub><b>Eşleşmeyi Kaldır</b></sub></td>
    <td align="center"><img src="docs/screenshots/user/settings.png" width="220"/><br/><sub><b>Kullanıcı Ayarları</b></sub></td>
  </tr>
  <tr>
    <td align="center"><img src="docs/screenshots/user/profile.png" width="220"/><br/><sub><b>Kullanıcı Profili</b></sub></td>
    <td align="center"><img src="docs/screenshots/user/change_nickname.png" width="220"/><br/><sub><b>Rumuz Değiştirme</b></sub></td>
    <td align="center"><img src="docs/screenshots/user/report_message.png" width="220"/><br/><sub><b>Mesaj Raporlama</b></sub></td>
    <td align="center"><img src="docs/screenshots/user/blocked_users.png" width="220"/><br/><sub><b>Engellenenler</b></sub></td>
  </tr>
  <tr>
    <td align="center"><img src="docs/screenshots/user/spam_protection_toast.png" width="220"/><br/><sub><b>Spam Koruması Uyarısı</b></sub></td>
    <td align="center"><img src="docs/screenshots/user/banned_nickname_notice.png" width="220"/><br/><sub><b>Yasaklı Rumuz Bildirimi</b></sub></td>
    <td align="center"><img src="docs/screenshots/user/system_banned_screen.png" width="220"/><br/><sub><b>Hesap Durduruldu Bildirimi</b></sub></td>
    <td align="center"><img src="docs/screenshots/user/unblock_confirm.png" width="220"/><br/><sub><b>Engeli Kaldır Onayı</b></sub></td>
  </tr>
</table>

### Kafe İşletmesi Ekranları

<table>
  <tr>
    <td align="center"><img src="docs/screenshots/business/business_login.png" width="220"/><br/><sub><b>İşletme Giriş Paneli</b></sub></td>
    <td align="center"><img src="docs/screenshots/business/dashboard_1.png" width="220"/><br/><sub><b>İşletme Dashboard</b></sub></td>
    <td align="center"><img src="docs/screenshots/business/cafe_chat.png" width="220"/><br/><sub><b>Canlı Sohbet İzleme</b></sub></td>
    <td align="center"><img src="docs/screenshots/business/active_chat_users.png" width="220"/><br/><sub><b>Aktif Kullanıcılar</b></sub></td>
  </tr>
  <tr>
    <td align="center"><img src="docs/screenshots/business/reports.png" width="220"/><br/><sub><b>Gelen Şikayetler</b></sub></td>
    <td align="center"><img src="docs/screenshots/business/ban_from_cafe.png" width="220"/><br/><sub><b>Kafeden Yasaklama</b></sub></td>
    <td align="center"><img src="docs/screenshots/business/ban_message.png" width="220"/><br/><sub><b>Susturma Cezası</b></sub></td>
    <td align="center"><img src="docs/screenshots/business/cafe_security.png" width="220"/><br/><sub><b>Kafe Güvenlik Merkezi</b></sub></td>
  </tr>
</table>

### Yönetici (Admin) Ekranları

<table>
  <tr>
    <td align="center"><img src="docs/screenshots/admin/stats.png" width="220"/><br/><sub><b>Platform İstatistikleri</b></sub></td>
    <td align="center"><img src="docs/screenshots/admin/add_cafe_1.png" width="220"/><br/><sub><b>Yeni Kafe Ekleme</b></sub></td>
    <td align="center"><img src="docs/screenshots/admin/cafe_created.jpg" width="220"/><br/><sub><b>QR Kod & Kafe Oluşumu</b></sub></td>
    <td align="center"><img src="docs/screenshots/admin/cafe_details.jpg" width="220"/><br/><sub><b>Kafe Detayları</b></sub></td>
  </tr>
  <tr>
    <td align="center"><img src="docs/screenshots/admin/users_list.png" width="220"/><br/><sub><b>Kullanıcı Listesi</b></sub></td>
    <td align="center"><img src="docs/screenshots/admin/ban_user.png" width="220"/><br/><sub><b>Kullanıcı Banlama</b></sub></td>
    <td align="center"><img src="docs/screenshots/admin/security_center.png" width="220"/><br/><sub><b>Güvenlik & Raporlar</b></sub></td>
    <td align="center"><img src="docs/screenshots/admin/edit_cafe_1.png" width="220"/><br/><sub><b>Kafe Düzenleme</b></sub></td>
  </tr>
</table>

---

## Teknoloji Yığını

| Katman | Teknoloji | Açıklama |
|--------|-----------|----------|
| **Backend** | Python 3.11+ / Flask | Modüler Application Factory mimarisi |
| **Gerçek Zamanlı İletişim** | Flask-SocketIO + Eventlet | Çift yönlü WebSocket ile anlık mesaj ve bildirim iletimi |
| **Veritabanı** | MySQL 8.x | İlişkisel veritabanı yönetim sistemi (utf8mb4) |
| **ORM Katmanı** | Flask-SQLAlchemy | Model tanımları, ilişkiler ve otomatik migration |
| **Güvenlik & CSRF** | Flask-WTF + Flask-Limiter | CSRF token doğrulama ve IP/Hesap bazlı hız sınırlaması |
| **Oturum & Kimlik** | Flask-Login + Werkzeug | Güvenli parola hash'leme (pbkdf2:sha256) ve oturum koruması |
| **Frontend** | HTML5 / CSS3 / Vanilla JS | Saf, hafif, modern karanlık temalı mobil öncelikli arayüz |
| **Konum & Mesafe** | Geolocation API + Haversine | GPS koordinat doğrulaması ve metre bazlı kafe çemberi denetimi |
| **QR Kod Üretimi** | Python qrcode[pil] + Pillow | Yüksek çözünürlüklü masa QR kodları oluşturma |
| **Çoklu Dil (i18n)** | Dahili i18n Motoru | Türkçe ve İngilizce dil desteği |

---

## Mimari Yapı

```
┌────────────────────────────────────────────────────────────┐
│               İstemci Katmanı (Tarayıcı / Mobil)           │
│                                                            │
│   Responsive UI  |  Vanilla JS  |  Socket.IO Client        │
└──────────────────────────┬─────────────────────────────────┘
                           │
                           │  HTTP / WebSocket (WSS)
                           │
┌──────────────────────────▼─────────────────────────────────┐
│               Python / Flask Web Uygulaması                 │
│                                                            │
│  Blueprints:                                               │
│  ├── /auth     (Kayıt, Giriş, SMS, İşletme Girişi)         │
│  ├── /chat     (Kafe Lobisi, Ortak Sohbet Odası)           │
│  ├── /dm       (Eşleşme İstekleri, Birebir Sohbet)         │
│  ├── /user     (Profil, Ayarlar, Engellenenler)            │
│  ├── /business (Kafe İşletme Paneli, Moderasyon)           │
│  └── /admin    (Kafe Oluşturma, QR Kod, Global Güvenlik)   │
│                                                            │
│  Socket.IO Olay Yöneticileri:                              │
│  ├── chat_events (send_message, join_room, report)         │
│  └── dm_events   (send_dm, match_request, unmatch)         │
└──────────────────────────┬─────────────────────────────────┘
                           │
                           │  SQLAlchemy ORM
                           │
┌──────────────────────────▼─────────────────────────────────┐
│                     MySQL Veritabanı                        │
│                                                            │
│  11 Tablo  |  İlişkisel Veri Modeli  |  utf8mb4 Desteği    │
└────────────────────────────────────────────────────────────┘
```

---

## Veritabanı Yapısı

Veritabanı SQLAlchemy modelleri ile tanımlanmış olup aşağıdaki 11 ana tablodan oluşur:

| Tablo | Açıklama |
|-------|----------|
| `users` | Tüm kullanıcılar (müşteriler, işletmeler, admin). Telefon, şifre hash'i, rol ve durum. |
| `cafes` | Tanımlı kafeler. İsim, slug, işletme kodu (`TLK-XXX`), GPS koordinatları ve QR yolu. |
| `cafe_sessions` | Kullanıcıların kafe odalarına giriş oturumları ve o kafedeki aktif rumuzları. |
| `messages` | Kafe genel sohbet odalarında gönderilen anlık mesajlar. |
| `direct_messages` | Eşleşen kullanıcılar arasındaki birebir özel mesajlar. |
| `dm_clearances` | Kullanıcıların kendi DM geçmişini temizleme durum kayıtları. |
| `match_requests` | Eşleşme istekleri ve durumları (`pending`, `accepted`, `rejected`, `unmatched`). |
| `reports` | Kural ihlali gerekçesiyle şikayet edilen mesaj ve kullanıcı raporları. |
| `bans` | Kafe bazlı veya sistem geneli kullanıcı ceza/yasaklama kayıtları. |
| `blocks` | Kullanıcıların birbirlerini engelleme kayıtları. |
| `cafe_stats` | Kafe bazında günlük oturum, mesaj ve etkileşim istatistikleri. |

---

## WebSocket ve API Mimarisi

Flask-SocketIO çift yönlü olay tabanlı mimari sunar:

| Olay Adı (Event) | Yön | Açıklama |
|------------------|-----|----------|
| `join` | İstemci → Sunucu | Kullanıcının kafe sohbet odasına katılması |
| `send_message` | İstemci → Sunucu | Kafe ortak odasına yeni mesaj gönderimi |
| `new_message` | Sunucu → İstemci | Odadaki tüm kullanıcılara mesajın anlık iletimi |
| `send_dm` | İstemci → Sunucu | Eşleşilen kullanıcıya özel mesaj gönderimi |
| `receive_dm` | Sunucu → İstemci | Alıcı kullanıcıya DM mesajının anlık teslimi |
| `match_request` | İstemci → Sunucu | Bir kullanıcıya eşleşme talebi iletilmesi |
| `match_request_received` | Sunucu → İstemci | Karşı tarafa anlık bildirim balonunun düşmesi |
| `match_accepted` | Sunucu → İstemci | Eşleşme kabul edildiğinde DM sekmesinin canlanması |
| `match_removed` | Sunucu → İstemci | Eşleşme kaldırıldığında ekranın anlık güncellenmesi |

---

## Kurulum ve Çalıştırma

### Gereksinimler

- [Python 3.11 veya üzeri](https://www.python.org/)
- [MySQL Server](https://dev.mysql.com/downloads/) veya [XAMPP](https://www.apachefriends.org/)
- [Git](https://git-scm.com/)

### 1. Projeyi Klonlayın

```bash
git clone https://github.com/jnost/Talknon.git
cd Talknon
```

### 2. Sanal Ortamı Oluşturun ve Kütüphaneleri Yükleyin

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Veritabanını Oluşturun

MySQL komut satırında veya phpMyAdmin'de boş veritabanını açın:

```sql
CREATE DATABASE talknon CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 4. Çevre Değişkenlerini Tanımlayın

`.env.example` dosyasını kopyalayarak `.env` adında yeni bir dosya oluşturun ve bilgilerinizi girin:

```env
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=super-secret-key-change-this

DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=mysql_sifreniz
DB_NAME=talknon

DEFAULT_ADMIN_PHONE=+905000000000
DEFAULT_ADMIN_PASSWORD=admin123
```

### 5. Uygulamayı Başlatın

```powershell
python run.py
```

*Uygulama ilk açılışta veritabanı tablolarını ve varsayılan yönetici hesabını otomatik olarak oluşturacaktır.*  
Tarayıcınızdan `http://localhost:5000` adresine girerek test etmeye başlayabilirsiniz.

---

## Proje Yapısı

```
Talknon/
├── app/
│   ├── blueprints/           # Modüler sayfa rotaları
│   │   ├── admin/            # Kafe tanımlama, kullanıcı denetimi, güvenlik
│   │   ├── auth/             # Müşteri ve işletme giriş/kayıt işlemleri
│   │   ├── business/         # Kafe işletmecisi paneli ve moderasyon
│   │   ├── chat/             # Kafe genel odası ve lobi yönetimi
│   │   ├── dm/               # Birebir özel sohbet ve eşleşmeler
│   │   └── user/             # Profil, ayarlar ve engellenen kullanıcılar
│   ├── models/               # SQLAlchemy veritabanı modelleri
│   ├── services/             # Harici servisler (Location, QR generator, Spam guard)
│   ├── socket_events/        # Anlık WebSocket olay yöneticileri
│   ├── static/               # CSS stilleri, Vanilla JS betikleri ve logolar
│   ├── templates/            # HTML arayüz şablonları
│   ├── utils/                # Yardımcı fonksiyonlar, dekoratörler, i18n
│   ├── config.py             # Development / Production yapılandırması
│   ├── extensions.py         # SQLAlchemy, SocketIO, Limiter eklentileri
│   └── __init__.py           # Flask App Factory ve veritabanı başlatıcı
├── docs/
│   └── screenshots/          # Dokümantasyon ekran görüntüleri
│       ├── admin/
│       ├── business/
│       └── user/
├── run.py                    # Uygulama ana başlatıcı scripti
├── requirements.txt          # Python paket bağımlılıkları
├── .env.example              # Örnek çevre değişkenleri
├── .gitignore
└── README.md
```

---

## Güvenlik ve Moderasyon

- **Şifreleme:** Kullanıcı şifreleri Werkzeug PBKDF2 (SHA-256) ile güvenli biçimde hash'lenir.
- **CSRF Koruması:** Tüm form gönderimleri `Flask-WTF` CSRF token koruması altındadır.
- **Rate Limiting (Hız Sınırı):** `Flask-Limiter` ile IP ve kullanıcı bazında spam engelleme uygulanır.
- **Geofence Mesafe Doğrulaması:** Haversine formülü ile GPS koordinatları kontrol edilerek uzaktan sahte katılımlar engellenir.
- **Admin & İşletme Yetki Kontrolü:** Tüm yönetimsel rotalar `@admin_required` ve `@business_required` dekoratörleri ile korunur.
- **Çift Taraflı İptal Güvenliği:** Eşleşme kaldırıldığında mesajlar ve konuşma kartları sayfa yenilenmeden dinamik olarak kaldırılır.

---

<p align="center">
  Copyright &copy; 2026 Erdem Özbalta. Tüm hakları saklıdır.<br/>
  <a href="mailto:erdemozbalta@gmail.com">erdemozbalta@gmail.com</a>
</p>
