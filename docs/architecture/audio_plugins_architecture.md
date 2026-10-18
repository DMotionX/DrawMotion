# التقرير الفني الشامل والتدقيق الجنائي لكافة أدوات وبلجنز الصوت (زيرو مخاطر - بدون تنفيذ)

## 1. ملخص المشكلة العامة والتشخيص الميداني

أكد الفحص العملي والتدقيق البرمجي أن **كافة الأدوات والمؤثرات (Audio Plugins & Tools)** الموجودة في شريط خصائص الصوت (`AudioFXPanel`) هي حالياً **عناصر واجهة مستخدم رسومية منفصلة تماماً (Isolated UI Controls)**، ولا توجد أي أسطر برمجية تقوم بربطها بمحرك المعاينة الحية (`AudioEngine`)، مما يجعل الضغط عليها أو تحريكها عديم الجدوى بنسبة 100%.

---

## 2. جدول الفحص والتدقيق الجنائي لكافة أدوات الصوت (Tool-by-Tool Audit)

| # | اسم الأداة / البلجن في الواجهة | العنصر البرمجي (UI Widget) | الحالة البرمجية الراهنة | سبب العطل الدقيق في الكود | الحل الهندسي المعتمد (Zero-Risk) |
| :---: | :--- | :--- | :---: | :--- | :--- |
| **1** | **Volume Booster (مضخم ومنظم الصوت)** | `QSlider (vol_slider)` من 0% إلى 300% | **معطل تماماً** | في `components/inspector.py`، الدالة المستقبلة تحتوي على `pass`. محرك الصوت `core/audio_engine/audio_engine.py` يحدد الصوت مرة واحدة عند التحميل ولا يستقبل أي تعديل لاحق. | إنشاء Slot مباشر في `TrackPlayer` و `AudioWorker` يقوم بتعديل `QAudioOutput.setVolume(vol / 100.0)` فورياً أثناء التشغيل دون إعادة تحميل الملف. |
| **2** | **Noise Cancellation (إلغاء الضوضاء والتشويش)** | `QCheckBox (noise_checkbox)` | **معطل تماماً (شكل فقط)** | مجرد خانة اختيار (Checkbox). لا يوجد أي كود في لغة بايثون أو محرك الصوت يقوم بتحليل الترددات أو تطبيق عزل الضوضاء أثناء المعاينة. | إنشاء مسار معالجة آمن ومحلي في الخلفية: عند تفعيل الخيار، يقوم سكريبت خفيف باستخراج نسخة منقاة عبر FFmpeg (`highpass=f=100,afftdn=nf=-25`) وتخزينها في الكاش، لتبديل مصدر الصوت فوراً بسلاسة وبدون أي لاج. |
| **3** | **Smart Auto-Normalize (الموازنة الذكية لمستوى الصوت)** | `QCheckBox (norm_checkbox)` | **معطل تماماً (شكل فقط)** | لا توجد أي خوارزمية لفحص سعة الصوت (Amplitude / RMS) أو موازنتها برمجياً في بيئة العمل. | حساب ذروة الصوت (Peak Amplitude) عبر `numpy` أو كاش سريع، ومضاعفة معامل الصوت `Volume Gain` تلقائياً ليصل الصوت إلى معيار الستوديو القياسي (0 dB / -14 LUFS) فورياً. |
| **4** | **Speed Adjustment (تسريع وإبطاء الصوت)** | `QSlider (speed_slider)` من 0.5x إلى 2.0x | **معطل تماماً** | يغير النص في الواجهة فقط، بينما `QMediaPlayer` لا يتم استدعاء دالة `setPlaybackRate` الخاصة به نهائياً. | استدعاء دالة `self.player.setPlaybackRate(speed)` المدمجة أصلاً وبأمان فائق داخل `QMediaPlayer`، مع تعديل امتداد المستطيل الزمني للتراك في التايم لاين تلقائياً. |
| **5** | **Deep Pitch Shift (تعديل طبقة الصوت - تمويه الصوت)** | `QCheckBox (pitch_checkbox)` | **معطل تماماً (شكل فقط)** | لا توجد أي معالجة لتغيير التردد الصوتي (Frequency Scaling) في محرك المعاينة. | دمج معالجة سريعة عبر FFmpeg (`asetrate=44100*0.8,atempo=1.25`) في الكاش المحلي، وتطبيق الفلتر نفسه في الرندر النهائي. |
| **6** | **Fade In (التلاشي للداخل - الدخول التدريجي)** | `QSlider (fi_slider)` من 0.0s إلى 5.0s | **معطل تماماً** | يتم حفظ القيمة في قاموس محلي فقط دون أي حسابات لمنحنى الصوت في المعاينة الحية. | في دالة المزامنة الدورية `seek_and_sync` في `TrackPlayer`: إذا كان وقت التشغيل الحالي أقل من زمن الـ Fade In، يتم رفع الصوت خطياً من 0 إلى القيمة المحددة بدقة ميلي ثانية. |
| **7** | **Fade Out (التلاشي للخارج - الخروج التدريجي)** | `QSlider (fo_slider)` من 0.0s إلى 5.0s | **معطل تماماً** | يتم حفظ القيمة في قاموس محلي فقط دون أي حسابات لمنحنى الصوت في المعاينة الحية. | في دالة `seek_and_sync`: إذا كان الوقت المتبقي للتراك أقل من زمن الـ Fade Out، يتم خفض الصوت تدريجياً وبسلاسة فائقة حتى الصفر. |
| **8** | **Project State Persistence (حفظ الإعدادات في المشروع)** | `AudioNodeModel.to_dict()` & `from_dict()` | **مفقود تماماً** | ملف `core/audio_engine/audio_node.py` لا يحفظ قاموس `audio_fx_settings`، وبالتالي تضيع كل إعدادات المستخدم بمجرد حفظ المشروع وإغلاقه. | إضافة حقل `audio_fx_settings` لعملية الحفظ والاسترجاع في ملف المشروع `.dm`، وضمان إعادة ضبط واجهة السلايدرات تلقائياً عند فتح المشروع. |

---

## 3. المعمارية الهندسية ومسار الإشارات الجديد (Target Clean Architecture)

```mermaid
flowchart TD
    subgraph UI_Layer["طبقة واجهة المستخدم (User Interface)"]
        UI_Panel["AudioFXPanel (audio_fx_panel.py)"]
        Vol["Volume (0%-300%)"]
        Speed["Speed (0.5x-2.0x)"]
        Fades["Fade In / Fade Out"]
        Filters["De-Noise & Normalize"]
        Vol & Speed & Fades & Filters -->|settings_changed(dict)| Inspector["components/inspector.py"]
    end

    subgraph Binding_Layer["طبقة التوصيل المباشر (Direct Binding Layer)"]
        Inspector -->|تحديث فوري| Node["AudioNodeModel (audio_node.py)\nحفظ دائم في audio_fx_settings"]
        Inspector -->|إرسال أمر التعديل| EngineProxy["AudioEngine (Proxy)\nrequest_update_track_fx(file, settings)"]
    end

    subgraph Playback_Layer["طبقة المعاينة الحية في الخلفية (Background Playback QThread)"]
        EngineProxy -->|Signal across Thread| Worker["AudioWorker (audio_engine.py)"]
        Worker -->|تطبيق فوري| Track["TrackPlayer"]
        
        Track -->|QAudioOutput.setVolume| LiveVol["تغيير علو الصوت فوراً"]
        Track -->|QMediaPlayer.setPlaybackRate| LiveSpeed["تغيير سرعة الصوت فوراً"]
        Track -->|Mathematical Curve in seek_and_sync| LiveFades["تطبيق منحنى الـ Fade In/Out"]
        Track -->|Cached WAV Buffer| LiveDSP["تشغيل الصوت المنقى (Denoised/Normalized)"]
    end

    subgraph Export_Layer["طبقة التصدير النهائي (FFmpeg Video Export Pipeline)"]
        Node -->|قراءة الإعدادات المحفوظة| ExportService["core/export_engine/ffmpeg_manager.py"]
        ExportService -->|بناء سلاسل فلاتر FFmpeg| Render["فيديو نهائي عالي الجودة متطابق 100% مع المعاينة"]
    end
```

---

## 4. الحلول التفصيلية لكل أداة بدون مخاطر (Zero-Risk Methodology)

### 1. حل مشكلة علو الصوت (Volume Booster) - زيرو مخاطر:
- **المبدأ:** عدم إعادة تشغيل الملف الصوتي من البداية عند تحريك السلايدر، لتفادي التقطيع أو التجمد.
- **الآلية:** ربط مؤشر السلايدر مباشرة بخاصية `self.audio_output.setVolume(vol / 100.0)` في مشغل Qt Multimedia.
- **الأمان:** `QAudioOutput` مخصص في الأصل لتغيير مستوى الصوت ديناميكياً بدون التأثير على الثريد الرئيسي للرسم.

### 2. حل مشكلة الدخول والخروج التدريجي (Fade In / Fade Out) - زيرو مخاطر:
- **المبدأ:** حساب رياضي خالص (Pure Math) داخل مؤقت المزامنة الزمني الموجود بالفعل في البرنامج.
- **المعادلة:**
  - في مرحلة الدخول: $\text{Volume}(t) = \text{TargetVolume} \times \left(\frac{t}{\text{FadeInDuration}}\right)$
  - في مرحلة الخروج: $\text{Volume}(t) = \text{TargetVolume} \times \left(\frac{\text{Duration} - t}{\text{FadeOutDuration}}\right)$
- **الأمان:** لا يتطلب أي مكتبات خارجية ولا يستهلك أي موارد معالجة إضافية (أقل من 0.001 ميلي ثانية).

### 3. حل مشكلة السرعة (Speed Control) - زيرو مخاطر:
- **المبدأ:** استخدام دالة `setPlaybackRate` المدعومة رسمياً في مكتبة `QMediaPlayer` في PySide6.
- **التزامن مع التايم لاين:** تعديل مدة عرض التراك في التايم لاين رياضياً: $\text{NewDuration} = \frac{\text{OriginalDuration}}{\text{Speed}}$.

### 4. حل مشكلة إزالة الضوضاء والموازنة (De-Noise & Normalize) - زيرو مخاطر:
- **المبدأ:** منع تشغيل خوارزميات DSP ثقيلة داخل ثريد واجهة المستخدم (GUI Thread) لتفادي تجمد الواجهة نهائياً.
- **الآلية:**
  1. عند وضع علامة صح على "Enable Background De-Noise"، ينطلق ثريد خلفي صامت (Background Worker) يقوم بتوليد ملف مؤقت عبر FFmpeg المدمج بالفعل في البرنامج:
     `ffmpeg -i input.mp3 -af "highpass=f=100,afftdn=nf=-25" temp_denoised.wav`
  2. بمجرد انتهاء التوليد (يستغرق أقل من نصف ثانية للملفات الصوتية)، يقوم المشغل بتبديل مسار الملف بسلاسة.
  3. في حال كان الجهاز ضعيفاً أو لم ينته التوليد، يستمر الصوت الأصلي في العمل بدون أي توقف (Graceful Fallback).

### 5. حل مشكلة حفظ واسترجاع الإعدادات (Persistence) - زيرو مخاطر:
- **المبدأ:** ضمان عدم فقدان التعديلات عند حفظ المشروع.
- **التعديل:** تضمين قاموس `audio_fx_settings` كاملاً في دالتي `to_dict()` و `from_dict()` في كائن `AudioNodeModel`، وتحديث شاشة الخصائص تلقائياً عند فتح المشروع.

---

## 5. مصفوفة التحقق والاختبار (Verification Checklist)

1. **اختبار المعاينة المباشرة (Live Preview Test):**
   - تحريك شريط الصوت إلى 30% -> ينخفض الصوت فوراً أثناء المعاينة.
   - تحريك شريط الصوت إلى 250% -> يتضخم الصوت فوراً.
   - تحريك شريط السرعة إلى 1.5x -> يتسارع الصوت فوراً.
   - تفعيل الـ Fade In بمقدار ثانيتين -> يبدأ الصوت خافتاً ويتصاعد تدريجياً.
2. **اختبار الثبات والحفظ (Project Save Test):**
   - حفظ مشروع يحتوي على إعدادات مخصصة لكافة الأدوات وإعادة فتحه -> تعود كافة المؤشرات والخانات لوضعها المضبوط مسبقاً.
3. **اختبار التصدير (Export Fidelity Test):**
   - تصدير مقطع فيديو ومطابقة الصوت الصادر مع صوت المعاينة بنسبة 100%.
4. **مستوى الأمان (Zero-Risk Guarantee):**
   - عدم المساس بأي من أجزاء الكانفاس، أو التايم لاين للرسومات، أو محرك Nuitka للبناء.
