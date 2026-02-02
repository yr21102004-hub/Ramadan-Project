from flask import Blueprint, render_template, request, jsonify
from flask_login import current_user
from models import ContactModel, SecurityLogModel

contact_model = ContactModel()
security_log_model = SecurityLogModel()

web_bp = Blueprint('web', __name__)

SERVICES_DATA = {
    'modern-paints': {
        'title': 'دهانات حديثة',
        'description': 'نستخدم أحدث تقنيات الدهانات الديكورية والكمبيوتر لإضفاء لمسة جمالية فريدة على منزلك. لدينا مجموعة واسعة من الألوان والتأثيرات التي تناسب جميع الأذواق، سواء كنت تبحث عن طابع كلاسيكي أو مودرن.',
        'features': [
            'دهانات جوتن وسايبس عالية الجودة',
            'دهانات قطيفة وشمواه',
            'تنسيق ألوان احترافي'
        ],
        'image': 'modern_paints.png'
    },
    'gypsum-board': {
        'title': 'جبس بورد (تشطيب ودهانات)',
        'description': 'نقدم أرقى مستويات التشطيب لأعمال الجبس بورد والأسقف المعلقة. تخصصنا هو إظهار جمال التصميم من خلال مراحل المعجون والدهانات الدقيقة، لضمان سطح ناعم ومثالي يبرز روعة الإضاءة والتصميم. (نحن متخصصون في بند الدهانات والتشطيب وليس التركيب).',
        'features': [
            'معالجة فواصل الجبس بورد بمهارة عالية',
            'تشطيب ناعم (Full Finish) للأسقف ومكتبات الشاشات',
            'تنسيق ألوان الدهانات مع الإضاءة المخفية',
            'دهانات عالية الجودة تدوم طويلاً'
        ],
        'image': 'gypsum_finish.png'
    },
    'integrated-finishing': {
        'title': 'تشطيب متكامل',
        'description': 'خدمة تشطيب ودهانات متكاملة تضمن لك جودة عالية ولمسات فنية راقية. نهتم بأدق التفاصيل لضمان مظهر جمالي يتناسب مع ذوقك الرفيع، سواء للواجهات الخارجية أو الديكورات الداخلية.',
        'features': [
            'تشطيب دهانات بكافة انواعها داخلية و خارجية',
            'أعمال المحارة والجبس',
            'ديكورات وتجاليد حوائط'
        ],
        'image': 'integrated_finishing.png'
    },
    'putty-finishing': {
        'title': 'تشطيب كامل ومعجون',
        'description': 'تعتبر مرحلة المعجون هي الأساس لأي دهان ناجح. نحن نولي اهتماماً خاصاً لهذه المرحلة، حيث نقوم بتجهيز الحوائط بمهارة فائقة لضمان ملمس ناعم كالحرير وخالٍ من العيوب.',
        'features': [
            'سحب طبقات معجون متعددة لتسوية الحوائط',
            'صنفرة ميكانيكية ويدوية لإزالة الشوائب',
            'علاج عيوب المحارة والزوايا',
            'دهانات أساس (سيلر) عالية الجودة'
        ],
        'image': 'putty_finishing.png'
    },
    'wallpaper': {
        'title': 'تركيب ورق حائط',
        'description': 'أضف لمسة من الفخامة إلى غرفتك مع أحدث تشكيلات ورق الحائط. فنيونا محترفون في التركيب لضمان عدم وجود فواصل ظاهرة أو فقاعات هواء، مع الحفاظ على تناسق النقوش.',
        'features': [
            'تركيب جميع أنواع الورق (فينيل، قماش، 3D)',
            'تجهيز الحوائط قبل التركيب لضمان الثبات',
            'دقة متناهية في قص ولصق الأطراف',
            'تصميمات عصرية وكلاسيكية'
        ],
        'image': 'wallpaper.png'
    },
    'renovation': {
        'title': 'تجديد وترميم',
        'description': 'نعيد الحياة للمنازل والمباني القديمة. نقوم بمعالجة كافة مشاكل الرطوبة والشروخ، وتحديث شبكات المرافق، وتغيير الديكور بالكامل ليواكب أحدث الصيحات.',
        'features': [
            'علاج الشروخ وتصدعات الجدران',
            'حلول جذرية لمشاكل الرطوبة والنشع',
            'تحديث الأرضيات والدهانات',
            'إعادة توزيع الكهرباء والسباكة'
        ],
        'image': 'renovation.jpg'
    }
}

@web_bp.route('/')
def index():
    return render_template('home.html')

@web_bp.route('/service/<service_id>')
def service_detail(service_id):
    service = SERVICES_DATA.get(service_id)
    if not service:
        return render_template('404.html'), 404
        
    # Log this view for analytics
    security_log_model.create('Service View', f'User viewed service: {service["title"]}', severity="info")
    
    return render_template('service_detail.html', service=service)

@web_bp.route('/about')
def about():
    return render_template('about.html')

@web_bp.route('/services')
def services():
    return render_template('services.html')


PROJECTS_DATA = {
    'apartments': {
        'title': 'بنود دهانات الشقق السكنية',
        'sections': [
            {
                'title': 'تجهيز الأسطح',
                'items': [
                    'تنظيف الحوائط والأسقف من الأتربة والزيوت.',
                    'معالجة الشروخ والتعشيش.',
                    'سكينة معجون طبقتين لتحقيق الاستواء والنعومة المطلوبة.',
                    'دهان طبقة أساس مناسبة لنوع السطح.'
                ]
            },
            {
                'title': 'الدهانات النهائية',
                'items': [
                    'دهان نهائي عدد (2–3) طبقات من دهانات بلاستيك عالية الجودة للحوائط والأسقف.',
                    'دهان النجارة المعدنية والأبواب بطبقة أساس مضادة للصدأ ثم طبقتين دهان نهائي.',
                    'الالتزام بدرجات الألوان المعتمدة وتحقيق مستوى تشطيب اقتصادي إلى متوسط مطابق للمواصفات القياسية.'
                ]
            }
        ]
    },
    'villas': {
        'title': 'بنود دهانات الفيلات والقصور',
        'sections': [
            {
                'title': 'تجهيز الأسطح (High End)',
                'items': [
                    'تنظيف شامل للأسطح.',
                    'معالجة دقيقة لجميع الشروخ والفواصل.',
                    'تنفيذ سكينة معجون متعددة الطبقات مع الصنفرة لتحقيق أعلى درجة نعومة.',
                    'دهان طبقات أساس متخصصة حسب نوع السطح.'
                ]
            },
            {
                'title': 'الدهانات الفاخرة والديكورية',
                'items': [
                    'تنفيذ دهانات نهائية فاخرة عدد (3–4) طبقات باستخدام خامات عالية الجودة.',
                    'تنفيذ دهانات ديكورية خاصة حسب التصميم المعماري (ستوكو، فينيسيان بلاستر، ماربل إفكت).',
                    'دهانات زخرفية للأعمدة والكورنيش.',
                    'دهان جميع العناصر المعمارية والزخرفية بدقة عالية لتحقيق أعلى مستوى تشطيب فاخر.'
                ]
            }
        ]
    },
    'companies': {
        'title': 'بنود دهانات الشركات والمباني الإدارية',
        'sections': [
            {
                'title': 'تجهيز الأسطح',
                'items': [
                    'تجهيز الأسطح بالطرق القياسية ومعالجة جميع العيوب السطحية.',
                    'تنفيذ سكينة معجون طبقتين لتحقيق سطح مستوٍ مناسب للأعمال الإدارية.',
                    'دهان طبقة أساس مناسبة.'
                ]
            },
            {
                'title': 'الدهانات العملية',
                'items': [
                    'دهان نهائي عدد (2–3) طبقات من دهانات عملية (سهلة التنظيف، مقاومة للاحتكاك).',
                    'استخدام ألوان رسمية هادئة متوافقة مع الهوية البصرية للمؤسسة.',
                    'دهان السلالم والممرات بدهانات مقاومة للاهتراء مع مراعاة اشتراطات السلامة ومقاومة الحريق عند الطلب.'
                ]
            }
        ]
    },
    'hotels': {
        'title': 'بنود دهانات الفنادق',
        'sections': [
            {
                'title': 'التجهيز الفندقي',
                'items': [
                    'تجهيز جميع الأسطح بدرجة عالية من الدقة لتحقيق تشطيب فندقي متجانس.',
                    'معالجة جميع الفواصل والشروخ بمواد مرنة لمنع التشققات المستقبلية.',
                    'تنفيذ سكينة معجون متعددة الطبقات مع الصنفرة الدقيقة.',
                    'دهان طبقات أساس متخصصة مقاومة للرطوبة والبكتيريا في المناطق الحساسة.'
                ]
            },
            {
                'title': 'الدهانات والمواصفات',
                'items': [
                    'دهان نهائي عدد (3–4) طبقات من دهانات عالية الجودة (مقاومة للبقع، سهولة التنظيف، ثبات لون عالي).',
                    'الالتزام باشتراطات السلامة ومقاومة الحريق طبقاً لكود الفنادق.',
                    'تنفيذ دهانات ديكورية خاصة في اللوبيات والأجنحة حسب التصميم المعماري.'
                ]
            }
        ]
    },
    'factories': {
        'title': 'بنود دهانات المصانع والمنشآت الصناعية',
        'sections': [
            {
                'title': 'تجهيز الأسطح الصناعية',
                'items': [
                    'تنظيف ميكانيكي أو رملي للأسطح المعدنية والخرسانية.',
                    'إزالة الصدأ والزيوت والملوثات الصناعية.',
                    'دهان طبقة برايمر صناعي متخصص حسب نوع السطح.'
                ]
            },
            {
                'title': 'الدهانات الصناعية والأرضيات',
                'items': [
                    'تنفيذ دهانات نهائية صناعية (إيبوكسي، بولي يوريثان) لمقاومة الكيماويات والزيوت والرطوبة والحرارة.',
                    'تنفيذ دهانات أرضيات صناعية إيبوكسي حسب مناطق التشغيل.',
                    'دهان إرشادي لتحديد مسارات الحركة ومناطق الخطر ومناطق التخزين.',
                    'الالتزام الكامل باشتراطات السلامة الصناعية والكود الفني المعتمد.'
                ]
            }
        ]
    }
}

@web_bp.route('/projects')
def projects():
    return render_template('projects.html')

@web_bp.route('/project/<category>')
def project_detail(category):
    project = PROJECTS_DATA.get(category)
    if not project:
        return render_template('404.html'), 404
        
    security_log_model.create('Project View', f'User viewed project category: {project["title"]}', severity="info")
    return render_template('project_detail.html', project=project)

@web_bp.route('/contact')
def contact():
    return render_template('contact.html')

@web_bp.route('/api/contact', methods=['POST'])
def contact_api():
    try:
        data = request.json
        name = data.get('name')
        phone = data.get('phone')
        message = data.get('message')
        service = data.get('service', 'عام')
        
        if not name or not phone or not message:
            return jsonify({'error': 'Missing required fields'}), 400
        
        user_id = current_user.username if current_user.is_authenticated else None
        
        contact_model.create(name, phone, message, user_id, service)
        return jsonify({'message': 'Success'}), 200
    except Exception as e:
        print(f"Error saving contact: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500
