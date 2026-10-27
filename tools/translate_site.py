"""Build the English pages from the Bulgarian source pages.

  website/index.html   -> en.html
  website/privacy.html -> privacy-en.html

Run after every change to a Bulgarian page:  python3 tools/translate_site.py
Each Bulgarian phrase must exist in its page; the script stops if one is
missing or if any Cyrillic text is left untranslated.
"""
import re
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent / "website"

# (Bulgarian, English). Longer phrases are replaced first.
T_INDEX = [
    # head, navigation, accessibility labels
    ('<html lang="bg">', '<html lang="en">'),
    ("<title>СТМ Лайф-04 | Служба по трудова медицина</title>",
     "<title>Life-04 | Occupational Health Service</title>"),
    ("СТМ „Лайф-04“ ООД – регистрирана служба по трудова медицина от 2004 г. Оценка на риска, медицинско наблюдение, обучения и документация по ЗЗБУТ в 15 области на България.",
     "Life-04 – a registered occupational health service in Bulgaria since 2004. Risk assessment, health surveillance, training and health & safety documentation in 15 regions."),
    ('aria-label="Лайф-04 – начало"', 'aria-label="Life-04 – home"'),
    ("<span>Лайф-04<small>Служба по трудова медицина</small></span>",
     "<span>Life-04<small>Occupational Health Service</small></span>"),
    ('aria-label="Език"', 'aria-label="Language"'),
    ('aria-label="Меню"', 'aria-label="Menu"'),
    ('aria-label="Надолу"', 'aria-label="Scroll down"'),
    ('<a href="#about">За нас</a>', '<a href="#about">About</a>'),
    ('<a href="#services">Услуги</a>', '<a href="#services">Services</a>'),
    ('<a href="#process">Как работим</a>', '<a href="#process">How we work</a>'),
    ('<a href="#experience">Опит</a>', '<a href="#experience">Experience</a>'),
    ('<a href="#team">Екип</a>', '<a href="#team">Team</a>'),
    ('class="btn btn-primary">Изпрати запитване</a>', 'class="btn btn-primary">Send enquiry</a>'),

    # hero
    ("Служба по трудова медицина · от 2004 г.", "Occupational health service · since 2004"),
    ("<h1>Над <em>20 години</em> грижа за здравето и безопасността на работещите</h1>",
     "<h1>Over <em>20 years</em> of caring for the health and safety of working people</h1>"),
    ("СТМ „Лайф-04“ поема цялата тема „здраве и безопасност при работа“ – от оценката на риска до медицинските прегледи и обученията. Вие се занимавате с бизнеса си, документите ви са готови за проверка във всеки момент.",
     "Life-04 takes care of everything related to health and safety at work – from risk assessment to medical check-ups and training. You run your business; your documents are ready for inspection at any time."),
    ("Безплатен преглед на документите <svg", "Free document review <svg"),
    (">Вижте услугите</a>", ">See our services</a>"),
    ("<span>години на пазара, без прекъсване</span>", "<span>years in the market, without interruption</span>"),
    ("<span>области в България, които обслужваме на място</span>", "<span>regions in Bulgaria served on site</span>"),
    ("<span>9001 сертифицирана система за управление на качеството</span>", "<span>9001 certified quality management system</span>"),

    # law
    (">Защо това е важно за вас</span>", ">Why this matters to you</span>"),
    (">Законът изисква три неща от всеки работодател</h2>", ">The law requires three things from every employer</h2>"),
    ("<h3>Оценка на риска</h3>\n        <p>За всяко работно място, с програма от мерки. Актуализира се при всяка промяна на хора, машини или помещения.</p>",
     "<h3>Risk assessment</h3>\n        <p>For every workplace, with a programme of measures. Updated whenever people, machines or premises change.</p>"),
    ("<h3>Медицинско наблюдение</h3>\n        <p>Прегледи при постъпване и периодично, заключения за годност и здравни досиета за всеки служител.</p>",
     "<h3>Health surveillance</h3>\n        <p>Pre-employment and periodic check-ups, fitness-for-work decisions and a health record for every employee.</p>"),
    ("<h3>Обучения и инструктажи</h3>\n        <p>На ръководители, на лицата, които инструктират, и на комитета по условия на труд. Всяка година.</p>",
     "<h3>Training and briefings</h3>\n        <p>For managers, for the people who brief staff and for the working conditions committee. Every year.</p>"),
    ("При проверка от Инспекцията по труда това са първите документи, които се искат. Липсата им води до предписания и глоби, а изготвянето им „в последния момент“ излиза по-скъпо от редовното обслужване.",
     "These are the first documents the Labour Inspectorate asks for during an inspection. Missing them leads to orders and fines, and preparing them at the last minute costs more than regular service."),

    # about
    (">Кои сме ние</span>", ">Who we are</span>"),
    ("<h2>Регистрирана служба по трудова медицина с над 20 години практика</h2>",
     "<h2>A registered occupational health service with over 20 years of practice</h2>"),
    ("Член сме на Сдружението на службите по трудова медицина в България.",
     "We are a member of the Association of Occupational Health Services in Bulgaria."),
    ("Управителят д-р Людмила Тенева е лекар и водещ одитор по ISO 9001, ISO 14001 и ISO 45001 с над 20 години опит. Това означава, че документите ви се изготвят от човек, който знае какво проверяват и одиторите, и Инспекцията по труда.",
     "Our managing director, Dr Lyudmila Teneva, is a physician and lead auditor for ISO 9001, ISO 14001 and ISO 45001 with over 20 years of experience. Your documents are prepared by someone who knows what both auditors and the Labour Inspectorate check."),
    ("<span>година на пазара, без прекъсване</span>", "<span>in the market since, without interruption</span>"),
    ("<span>сертифицирана система за управление на качеството (2015)</span>", "<span>certified quality management system (2015)</span>"),
    ("<span>удостоверение от Министерството на здравеопазването</span>", "<span>registration certificate from the Ministry of Health</span>"),

    # benefits
    (">Какво получавате</span>", ">What you get</span>"),
    (">Един партньор, който поема цялата тема „здраве и безопасност“</h2>", ">One partner for everything health and safety</h2>"),
    ("<h3>Пълно нормативно съответствие</h3><p>Всички документи по Закона за здравословни и безопасни условия на труд са налични, актуални и готови за проверка във всеки момент.</p>",
     "<h3>Full legal compliance</h3><p>All documents required by the Bulgarian Health and Safety at Work Act are in place, up to date and ready for inspection at any time.</p>"),
    ("<h3>По-малко натоварване за екипа ви</h3><p>Ние водим документацията, прегледите и обученията. Вашият човек по безопасност има партньор, не още задачи.</p>",
     "<h3>Less workload for your team</h3><p>We handle the paperwork, check-ups and training. Your safety officer gets a partner, not more tasks.</p>"),
    ("<h3>Оценка на риска за вашата среда</h3><p>Не общ образец, а оценка от специалисти, които вече са работили в болници, заводи, строителни обекти, офиси и училища.</p>",
     "<h3>Risk assessment for your environment</h3><p>Not a generic template, but an assessment by specialists who have already worked in hospitals, factories, construction sites, offices and schools.</p>"),
    ("<h3>По-здрави и по-защитени служители</h3><p>Годишен анализ на здравословното състояние и конкретни мерки, които намаляват отсъствията и трудовите злополуки.</p>",
     "<h3>Healthier, better protected employees</h3><p>An annual health analysis and concrete measures that reduce sick leave and workplace accidents.</p>"),

    # services
    ('<span class="eyebrow reveal">Услуги</span>', '<span class="eyebrow reveal">Services</span>'),
    (">Четири области, покрити изцяло в абонамента</h2>", ">Four areas, fully covered by the subscription</h2>"),
    ("<use href=\"#i-search\"/></svg>Оценка на риска</button>", "<use href=\"#i-search\"/></svg>Risk assessment</button>"),
    ("<use href=\"#i-pulse\"/></svg>Медицинско наблюдение</button>", "<use href=\"#i-pulse\"/></svg>Health surveillance</button>"),
    ("<use href=\"#i-cap\"/></svg>Обучения</button>", "<use href=\"#i-cap\"/></svg>Training</button>"),
    ("<use href=\"#i-doc\"/></svg>Документация</button>", "<use href=\"#i-doc\"/></svg>Documentation</button>"),
    ("<h3>Оценка и управление на риска</h3>", "<h3>Risk assessment and management</h3>"),
    ("Програма и карти за оценка на риска", "Risk assessment programme and workplace risk cards"),
    ("Оценка по Наредба № 5/1999 г.", "Assessment under Ordinance No. 5/1999"),
    ("Програма с мерки за намаляване на риска", "Programme of risk reduction measures"),
    ("Физиологичен режим на труд и почивка", "Work and rest schedules"),
    ('<div class="num">02</div><h3>Медицинско наблюдение</h3>', '<div class="num">02</div><h3>Health surveillance</h3>'),
    ("Годишен план за периодичните прегледи", "Annual plan for periodic check-ups"),
    ("Заключения за годност при постъпване", "Fitness-for-work decisions for new hires"),
    ("Здравни досиета на всеки служител", "A health record for every employee"),
    ("Годишен анализ на здравословното състояние", "Annual analysis of employee health"),
    ('<div class="num">03</div><h3>Обучения</h3>', '<div class="num">03</div><h3>Training</h3>'),
    ("Ръководители и инструктиращи (Наредба РД-07-2)", "Managers and instructors (Ordinance RD-07-2)"),
    ("Комитети и групи по условия на труд", "Working conditions committees and groups"),
    ("Длъжностни лица по Наредба № 3/1998 г.", "Designated officers under Ordinance No. 3/1998"),
    ("Информиране на служителите за рисковете", "Informing employees about the risks"),
    ("<h3>Документация и становища</h3>", "<h3>Documentation and expert opinions</h3>"),
    ("Преглед и актуализация на заповедите по ЗЗБУТ", "Review and update of internal health & safety orders"),
    ("Правила и инструкции за безопасна работа", "Safe work rules and instructions"),
    ("Консултантски заключения по нормативни изисквания", "Advisory opinions on legal requirements"),
    ("Участие при трудови злополуки и професионални заболявания", "Support with workplace accidents and occupational diseases"),
    ("Пълният списък с всички услуги по Наредба № 3/2008 г. ще получите при поискване или на първата среща.",
     "The full list of services under Ordinance No. 3/2008 is available on request or at our first meeting."),

    # process
    (">Как работим</span>", ">How we work</span>"),
    (">Пет стъпки от първата среща до постоянното обслужване</h2>", ">Five steps from the first meeting to ongoing service</h2>"),
    ("<h3>Преглед на текущото състояние</h3><p>Оглед на обектите и на наличната документация. Казваме ви точно какво липсва.</p>",
     "<h3>Review of the current state</h3><p>We visit your sites and review existing documents. We tell you exactly what is missing.</p>"),
    ("<h3>Оценка на риска</h3><p>Идентифициране на опасностите, карти за всяко работно място, програма с мерки.</p>",
     "<h3>Risk assessment</h3><p>Identifying hazards, a risk card for every workplace, a programme of measures.</p>"),
    ("<h3>Медицинско наблюдение</h3><p>План за прегледите, здравни досиета, заключения за годност.</p>",
     "<h3>Health surveillance</h3><p>Check-up plan, health records, fitness-for-work decisions.</p>"),
    ("<h3>Обучения</h3><p>На ръководители, инструктиращи и комитет по условия на труд, с протоколи и удостоверения.</p>",
     "<h3>Training</h3><p>For managers, instructors and the working conditions committee, with minutes and certificates.</p>"),
    ("<h3>Текущо обслужване</h3><p>Актуализации при промяна на хора, работни места или закони. Годишен анализ.</p>",
     "<h3>Ongoing service</h3><p>Updates whenever people, workplaces or laws change. Annual analysis.</p>"),
    ("<strong>Един контакт за всичко.</strong> Получавате отговорен консултант, който познава обектите ви и отговаря в рамките на работния ден.",
     "<strong>One contact for everything.</strong> You get a dedicated consultant who knows your sites and replies within the working day."),

    # experience
    ('<span class="eyebrow reveal">Опит</span>', '<span class="eyebrow reveal">Experience</span>'),
    (">Познаваме рисковете във вашия отрасъл, защото вече сме работили в него</h2>", ">We know the risks in your industry because we have already worked in it</h2>"),
    ("Частни и държавни организации – от трима души на дистанционна работа до болници и строителни компании с хиляди служители.",
     "Private and public organisations – from three people working remotely to hospitals and construction companies with thousands of employees."),
    ("</svg>Здравеопазване</div>", "</svg>Healthcare</div>"),
    ("</svg>Строителство</div>", "</svg>Construction</div>"),
    ("</svg>Машиностроене</div>", "</svg>Mechanical engineering</div>"),
    ("</svg>Хранителна промишленост</div>", "</svg>Food industry</div>"),
    ("</svg>Образование и култура</div>", "</svg>Education and culture</div>"),
    ("</svg>Държавна администрация</div>", "</svg>Public administration</div>"),
    ("</svg>Телекомуникации и IT</div>", "</svg>Telecoms and IT</div>"),
    ("</svg>Търговия с горива</div>", "</svg>Fuel trading</div>"),
    ("</svg>Шивашка промишленост</div>", "</svg>Garment industry</div>"),
    ("</svg>Транспорт и логистика</div>", "</svg>Transport and logistics</div>"),
    ("</svg>Хотелиерство и ресторанти</div>", "</svg>Hotels and restaurants</div>"),
    ("</svg>Добив и геопроучване</div>", "</svg>Mining and geological exploration</div>"),

    # clients
    (">Клиенти</span>", ">Clients</span>"),
    (">Доверието на международни компании и публични институции</h2>", ">Trusted by international companies and public institutions</h2>"),
    ('alt="Победа"', 'alt="Pobeda"'),
    ('alt="ИАГ"', 'alt="IAG"'),

    # team
    (">Екип и покритие</span>", ">Team and coverage</span>"),
    ("<h2>Лекар, инженери и психолог – на място в 15 области</h2>", "<h2>A physician, engineers and a psychologist – on site in 15 regions</h2>"),
    ("<span>лекар с призната специалност по трудова медицина</span>", "<span>physician specialised in occupational medicine</span>"),
    ("<span>инженери и технически специалисти по безопасност на труда</span>", "<span>engineers and technical specialists in occupational safety</span>"),
    ("<span>специалист по трудова психология</span>", "<span>specialist in occupational psychology</span>"),
    ("Съставът отговаря на Наредба № 3/2008 г. Имаме вътрешна система за обучение и информационно осигуряване на консултантите.",
     "Our team meets the requirements of Ordinance No. 3/2008. We run an internal training and knowledge system for our consultants."),
    ("<h3>Обслужвани области</h3>\n      <p>Работим на място в обектите ви.</p>",
     "<h3>Regions we serve</h3>\n      <p>We work on site at your premises.</p>"),
    ("<span>София-град</span><span>Софийска област</span><span>Пловдив</span><span>Бургас</span><span>Стара Загора</span><span>Благоевград</span><span>Хасково</span><span>Кърджали</span><span>Сливен</span><span>Плевен</span><span>Ловеч</span><span>Перник</span><span>Кюстендил</span><span>Видин</span><span>Силистра</span>",
     "<span>Sofia City</span><span>Sofia Province</span><span>Plovdiv</span><span>Burgas</span><span>Stara Zagora</span><span>Blagoevgrad</span><span>Haskovo</span><span>Kardzhali</span><span>Sliven</span><span>Pleven</span><span>Lovech</span><span>Pernik</span><span>Kyustendil</span><span>Vidin</span><span>Silistra</span>"),
    ("<strong>Извън тези области?</strong> Работим и дистанционно за офисни екипи и хора на работа от вкъщи, а огледите на обекти се договарят отделно.",
     "<strong>Outside these regions?</strong> We also work remotely for office teams and people working from home; site visits are arranged separately."),

    # privacy
    (">Защита на личните данни</span>", ">Data protection</span>"),
    (">Здравните данни остават при нас. Вие получавате само заключението</h2>", ">Health data stays with us. You only receive the conclusion</h2>"),
    ("Здравните досиета са специална категория данни по Регламент (ЕС) 2016/679 и се съхраняват единствено от службата по трудова медицина.",
     "Health records are a special category of data under Regulation (EU) 2016/679 (GDPR) and are kept only by the occupational health service."),
    ("Работодателят получава заключение „годен / негоден / годен при условия“, а не диагнозите и резултатите зад него.",
     "The employer receives a conclusion – “fit / unfit / fit with conditions” – not the diagnoses and results behind it."),
    ("Достъп до системата TM SISTEM имат само обучени служители с парола, чиито задължения го изискват.",
     "Only trained, password-protected staff whose duties require it can access the TM SISTEM software."),
    ("Писмени процедури за достъп, съхранение, предаване и унищожаване на здравната документация.",
     "Written procedures for accessing, storing, transferring and destroying health records."),
    ("<h3>Какво подписваме с вас</h3>", "<h3>What we sign with you</h3>"),
    ("</svg>Договор за трудовомедицинско обслужване</div>", "</svg>Occupational health service agreement</div>"),
    ("</svg>Договор за обработване на лични данни</div>", "</svg>Data processing agreement</div>"),
    (">Какво вижда работодателят:</p>", ">What the employer sees:</p>"),
    ('<span class="v-ok">Годен</span><span class="v-cond">Годен при условия</span><span class="v-no">Негоден</span>',
     '<span class="v-ok">Fit</span><span class="v-cond">Fit with conditions</span><span class="v-no">Unfit</span>'),

    # why
    (">Защо Лайф-04</span>", ">Why Life-04</span>"),
    (">Четири неща, които ни отличават от стандартната служба</h2>", ">Four things that set us apart from a standard service</h2>"),
    ("<h3>Ръководи ни водещ одитор по ISO 45001</h3><p>Документите ви се пишат от човек, който сам проверява такива системи. Ако имате или планирате сертификация, това спестява месеци.</p>",
     "<h3>Led by an ISO 45001 lead auditor</h3><p>Your documents are written by someone who audits such systems herself. If you have or plan a certification, this saves months.</p>"),
    ("<h3>Оценка на риска по отрасъл, не по шаблон</h3><p>Експлозивен прах в мелница, легионела в болнична водна система, работа на височина при монтаж. Знаем какво да търсим.</p>",
     "<h3>Industry-specific risk assessment, not a template</h3><p>Explosive dust in a mill, legionella in a hospital water system, working at height during installation. We know what to look for.</p>"),
    ("<h3>Лицензиран софтуер за здравните досиета</h3><p>Работим със специализираната система TM SISTEM, с контролиран достъп и обучени служители. Нищо не е в папки по бюрата.</p>",
     "<h3>Licensed software for health records</h3><p>We use the specialised TM SISTEM software with controlled access and trained staff. Nothing sits in folders on desks.</p>"),
    ("<h3>Същият екип от 2004 г. насам</h3><p>Пряк контакт с управителя. Клиенти, с които работим над десет години, са нормата, а не изключение.</p>",
     "<h3>The same team since 2004</h3><p>Direct contact with the managing director. Clients who have worked with us for over ten years are the norm, not the exception.</p>"),

    # next steps
    (">Следващи стъпки</span>", ">Next steps</span>"),
    (">Три стъпки до подписан договор</h2>", ">Three steps to a signed contract</h2>"),
    ("<h3>Разговор от 20 минути</h3><p>Брой служители, обекти, какво имате към момента. По телефон или на място.</p>",
     "<h3>A 20-minute call</h3><p>Number of employees, sites, what you already have. By phone or in person.</p>"),
    ('<span class="tag">Безплатно</span>', '<span class="tag">Free</span>'),
    ("<h3>Преглед на документите</h3><p>Казваме ви какво липсва и какво би отбелязала Инспекцията по труда. Получавате това независимо дали подпишете с нас.</p>",
     "<h3>Document review</h3><p>We tell you what is missing and what the Labour Inspectorate would flag. You keep this whether or not you sign with us.</p>"),
    ("<h3>Оферта и договор</h3><p>Индивидуална оферта до 3 работни дни. При съгласие започваме в седмицата след подписване.</p>",
     "<h3>Offer and contract</h3><p>A tailored offer within 3 working days. Once agreed, we start the week after signing.</p>"),
    ("Предстои ви проверка или смяна на досегашната служба? <strong>", "Facing an inspection or switching from your current provider? <strong>"),
    (">Поемаме и текущи случаи с кратък срок.</strong>", ">We also take on urgent cases at short notice.</strong>"),

    # contact
    (">За контакт</span>", ">Contact</span>"),
    ("<h2>Свържете се с нас</h2>", "<h2>Get in touch</h2>"),
    ('<div class="avatar">ЛТ</div>', '<div class="avatar">LT</div>'),
    ("<b>Д-р Людмила Тенева</b><span>Управител, лекар по трудова медицина</span>",
     "<b>Dr Lyudmila Teneva</b><span>Managing director, occupational health physician</span>"),
    ("София 1309, ул. „Зайчар“ № 125, офис 2", "125 Zaychar St., office 2, 1309 Sofia, Bulgaria"),
    ("<h3>Изпрати запитване</h3>", "<h3>Send an enquiry</h3>"),
    ('<label>Име<input name="Име"', '<label>Name<input name="Name"'),
    ('<span>Фирма <span class="req"', '<span>Company <span class="req"'),
    ('<input name="Фирма"', '<input name="Company"'),
    ('<span>Телефон <span class="req"', '<span>Phone <span class="req"'),
    ('<input name="Телефон"', '<input name="Phone"'),
    ('title="Само цифри, интервали и +"', 'title="Digits, spaces and + only"'),
    ('<span>Имейл <span class="req"', '<span>Email <span class="req"'),
    ("'Моля, въведете валиден телефонен номер.'", "'Please enter a valid phone number.'"),
    ('<label>Брой служители\n        <select name="Брой служители">', '<label>Number of employees\n        <select name="Employees">'),
    ("<option>до 10</option><option>11 – 50</option><option>51 – 250</option><option>над 250</option>",
     "<option>up to 10</option><option>11 – 50</option><option>51 – 250</option><option>over 250</option>"),
    ('<label>Съобщение<textarea name="Съобщение"', '<label>Message<textarea name="Message"'),
    ('placeholder="Обекти, дейност, предстояща проверка…"', 'placeholder="Sites, line of business, upcoming inspection…"'),
    ('data-hl="bg"', 'data-hl="en"'),
    (">Изпратете запитване <svg", ">Send enquiry <svg"),
    ("Запитването се изпраща директно до office@life-04.com. Ще се свържем с вас в рамките на 2 работни дни.",
     "Your enquiry goes straight to office@life-04.com. We will get back to you within 2 working days."),

    # consent and footer
    ('href="privacy.html"', 'href="privacy-en.html"'),
    ("<span>Запознах се с <a", "<span>I have read the <a"),
    (">Политиката за поверителност</a> и знам как ще бъдат използвани данните ми.</span>",
     ">Privacy Policy</a> and know how my data will be used.</span>"),
    ("СТМ „Лайф-04“ ООД · ЕИК 123673206 · София 1309, ул. „Зайчар“ № 125 · Удостоверение № 052-3 от МЗ",
     "STM Life-04 Ltd · Company ID (EIK) 123673206 · 125 Zaychar St., 1309 Sofia, Bulgaria · Ministry of Health registration No. 052-3"),
    (">Политика за поверителност</a><a", ">Privacy Policy</a><a"),

    # form messages (script)
    ("' Можете да пишете и на office@life-04.com или да се обадите на +359 897 932 200.'",
     "' You can also email office@life-04.com or call +359 897 932 200.'"),
    ("'Благодарим! Запитването е изпратено. Ще се свържем с вас в рамките на 2 работни дни.'",
     "'Thank you! Your enquiry has been sent. We will get back to you within 2 working days.'"),
    ("'Благодарим! Запитването е изпратено.'", "'Thank you! Your enquiry has been sent.'"),
    ("'Моля, проверете данните и натиснете бутона отново.'", "'Please check your details and press the button again.'"),
    ("'Запитването ви вече е изпратено. Моля, изчакайте минута преди да изпратите ново.'",
     "'Your enquiry has already been sent. Please wait a minute before sending another one.'"),
    ("'Достигнат е лимитът от запитвания за един час.'", "'You have reached the limit of enquiries for this hour.'"),
    ("'Моля, премахнете връзките (линковете) от съобщението.'", "'Please remove the links from your message.'"),
    ("'Моля, потвърдете, че не сте робот.'", "'Please confirm that you are not a robot.'"),
    ("'Запитването не можа да бъде изпратено.'", "'Your enquiry could not be sent.'"),
    ("send.textContent='Изпращане…'", "send.textContent='Sending…'"),
    # the office reads Bulgarian: keep the email subject in Bulgarian, marked with the page language
    ("'Запитване за безплатен преглед – '", "'Запитване за безплатен преглед (EN) – '"),
]

T_PRIVACY = [
    ('<html lang="bg">', '<html lang="en">'),
    ("<title>Политика за поверителност | СТМ Лайф-04</title>", "<title>Privacy Policy | Life-04</title>"),
    ("Как СТМ „Лайф-04“ ООД обработва личните данни, изпратени чрез сайта.",
     "How STM Life-04 Ltd processes personal data sent through this website."),
    ('href="index.html"', 'href="en.html"'),
    ("</svg></span>Лайф-04</a>", "</svg></span>Life-04</a>"),
    ('aria-label="Език"', 'aria-label="Language"'),
    ("<h1>Политика за поверителност</h1>", "<h1>Privacy Policy</h1>"),
    ("В сила от 27 октомври 2026 г.", "Effective from 27 October 2026"),

    # 1. Scope
    ("<h2>1. Обхват</h2>", "<h2>1. Scope</h2>"),
    ("Тази политика описва как СТМ „Лайф-04“ ООД обработва личните данни на посетителите на уебсайта и на лицата, които ни изпращат запитване чрез формата за контакт.",
     "This policy describes how STM Life-04 Ltd processes the personal data of website visitors and of people who send us an enquiry through the contact form."),
    ("Политиката не се отнася до здравните данни на работниците и служителите на нашите клиенти. Те се обработват при трудовомедицинското обслужване по отделни правила, съобщени на засегнатите лица и уредени в договорите с клиентите.",
     "This policy does not cover the health data of our clients’ employees. That data is processed as part of occupational health services under separate rules, communicated to the people concerned and set out in our client contracts."),

    # 2. Controller and DPO
    ("<h2>2. Администратор и длъжностно лице по защита на данните</h2>", "<h2>2. Controller and Data Protection Officer</h2>"),
    ("<strong>Администратор:</strong> СТМ „Лайф-04“ ООД, ЕИК 123673206, седалище и адрес на управление: ",
     "<strong>Controller:</strong> STM Life-04 Ltd, company ID (EIK) 123673206, registered office: "),
    ('<mark class="todo">[според Търговския регистър]</mark>', '<mark class="todo">[as per the Commercial Register]</mark>'),
    (". Адрес за кореспонденция: гр. София 1309, ул. „Зайчар“ № 125, офис 2. Имейл: ",
     ". Correspondence address: 125 Zaychar St., office 2, 1309 Sofia, Bulgaria. Email: "),
    ("</a>. Телефон: +359 897 932 200.</p>", "</a>. Phone: +359 897 932 200.</p>"),
    ("<strong>Длъжностно лице по защита на данните:</strong> ", "<strong>Data Protection Officer:</strong> "),
    ('<mark class="todo">[име]</mark>, имейл: <mark class="todo">[имейл]</mark>', '<mark class="todo">[name]</mark>, email: <mark class="todo">[email]</mark>'),
    (". Можете да се обърнете към него по всички въпроси, свързани с личните ви данни и правата ви.",
     ". You can contact them about any question concerning your personal data and your rights."),

    # 3. Data
    ("<h2>3. Какви данни обработваме</h2>", "<h2>3. What data we process</h2>"),
    ("<strong>Данни, които въвеждате във формата:</strong>", "<strong>Data you enter in the form:</strong>"),
    ("<li>фирма, телефон и имейл (задължителни);</li>", "<li>company, phone and email (required);</li>"),
    ("<li>име, брой служители и текст на съобщението (по желание).</li>", "<li>name, number of employees and the text of your message (optional).</li>"),
    ("<strong>Технически данни:</strong> IP адрес, вид браузър и устройство, дата и час на посещението. Те се записват от хостинг доставчика и при проверката „Не съм робот“ (hCaptcha).",
     "<strong>Technical data:</strong> IP address, browser and device type, date and time of the visit. They are logged by the hosting provider and by the “I am human” check (hCaptcha)."),
    ("<strong>Данни в паметта на браузъра:</strong> часовете на изпратените запитвания през последния час. Те остават на вашето устройство и не се изпращат към нас.",
     "<strong>Data in browser storage:</strong> the times of enquiries sent in the last hour. They stay on your device and are not sent to us."),
    ("<strong>Здравни данни:</strong> не ги искаме и не са нужни за запитването. Моля, не включвайте в съобщението информация за здравето си или на други лица. Ако все пак получим такава информация, няма да я използваме и ще я изтрием без необосновано забавяне.",
     "<strong>Health data:</strong> we do not ask for it and it is not needed for an enquiry. Please do not include information about your health or anyone else’s in your message. If we receive such information anyway, we will not use it and will delete it without undue delay."),

    # 4. Purposes
    ("<h2>4. Цели и правни основания</h2>", "<h2>4. Purposes and legal bases</h2>"),
    ("Използваме данните само за целите по-долу. Не ги използваме за реклама и не ги продаваме.",
     "We use the data only for the purposes below. We do not use it for advertising and we do not sell it."),
    ("<tr><th>Цел</th><th>Правно основание (Регламент (ЕС) 2016/679)</th></tr>",
     "<tr><th>Purpose</th><th>Legal basis (Regulation (EU) 2016/679)</th></tr>"),
    ("<td>Отговор на запитването, изготвяне на оферта и преговори за договор</td>",
     "<td>Answering your enquiry, preparing an offer and negotiating a contract</td>"),
    ("<td>Ако запитвате от собствено име: стъпки преди сключване на договор по ваше искане (чл. 6, пар. 1, б. „б“). Ако пишете от името на фирма: нашият легитимен интерес да отговорим на представителя на потенциален клиент (чл. 6, пар. 1, б. „е“).</td>",
     "<td>If you enquire in your own name: steps taken at your request before entering into a contract (Art. 6(1)(b)). If you write on behalf of a company: our legitimate interest in replying to the representative of a prospective client (Art. 6(1)(f)).</td>"),
    ("<td>Защита на формата и сайта от спам, злоупотреби и атаки</td>", "<td>Protecting the form and the website from spam, abuse and attacks</td>"),
    ("<td>Нашият легитимен интерес да поддържаме сайта сигурен и работещ (чл. 6, пар. 1, б. „е“).</td>",
     "<td>Our legitimate interest in keeping the website secure and working (Art. 6(1)(f)).</td>"),
    ("<td>Спазване на законови задължения, например счетоводни след сключване на договор</td>",
     "<td>Complying with legal obligations, such as accounting after a contract is signed</td>"),
    ("<td>Законово задължение (чл. 6, пар. 1, б. „в“).</td>", "<td>Legal obligation (Art. 6(1)(c)).</td>"),
    ("<td>Установяване, упражняване или защита на правни претенции</td>", "<td>Establishing, exercising or defending legal claims</td>"),
    ("<td>Нашият легитимен интерес (чл. 6, пар. 1, б. „е“).</td>", "<td>Our legitimate interest (Art. 6(1)(f)).</td>"),

    # 5. Required data
    ("<h2>5. Задължителни данни</h2>", "<h2>5. Required data</h2>"),
    ("Предоставянето на данни чрез формата е доброволно. Няма законово или договорно задължение да ги предоставите.",
     "Providing data through the form is voluntary. There is no legal or contractual obligation to provide it."),
    ("Фирмата, телефонът и имейлът са нужни, за да ви отговорим. Без тях формата не може да бъде изпратена. Можете да ни пишете и на ",
     "Company, phone and email are needed so we can reply. Without them the form cannot be sent. You can also write to us at "),
    ("</a> или да се обадите на +359 897 932 200.</p>", "</a> or call +359 897 932 200.</p>"),

    # 6. Retention
    ("<h2>6. Срокове на съхранение</h2>", "<h2>6. Retention periods</h2>"),
    ("<tr><th>Данни</th><th>Срок</th></tr>", "<tr><th>Data</th><th>Period</th></tr>"),
    ("<td>Запитване, след което не е сключен договор</td><td>До 12 месеца след последния контакт.</td>",
     "<td>Enquiry not followed by a contract</td><td>Up to 12 months after the last contact.</td>"),
    ("<td>Запитване, след което е сключен договор</td><td>За срока на договора и 5 години след прекратяването му (общата давност по чл. 110 от Закона за задълженията и договорите).</td>",
     "<td>Enquiry followed by a contract</td><td>For the term of the contract and 5 years after it ends (the general limitation period under Art. 110 of the Bulgarian Obligations and Contracts Act).</td>"),
    ("<td>Счетоводни документи по сключен договор</td><td>10 години (чл. 12 от Закона за счетоводството).</td>",
     "<td>Accounting records for a signed contract</td><td>10 years (Art. 12 of the Bulgarian Accountancy Act).</td>"),
    ("<td>Технически данни в записите на хостинга и hCaptcha</td><td>Според сроковете, определени от съответния доставчик.</td>",
     "<td>Technical data in hosting and hCaptcha logs</td><td>According to the periods set by the provider concerned.</td>"),
    ("<td>Данни в паметта на браузъра</td><td>Използват се само за последния час. Можете да ги изтриете през настройките на браузъра си.</td>",
     "<td>Data in browser storage</td><td>Used only for the last hour. You can delete them in your browser settings.</td>"),
    ("Ако има започнал спор или проверка, пазим нужните данни до приключването му. След изтичането на срока данните се изтриват или анонимизират.",
     "If a dispute or inspection is under way, we keep the data needed until it is closed. When the period ends, the data is deleted or anonymised."),

    # 7. Recipients
    ("<h2>7. Получатели</h2>", "<h2>7. Recipients</h2>"),
    ("До данните имат достъп само служителите на дружеството, които отговарят на запитванията. За да работи сайтът, ползваме следните обработващи. Те обработват данни само по наши указания и са свързани с договор по чл. 28 от Регламента.",
     "Only the company’s staff who answer enquiries have access to the data. To run the website we use the following processors. They process data only on our instructions and are bound by a contract under Art. 28 of the Regulation."),
    ("<tr><th>Обработващ</th><th>За какво</th><th>Какви данни</th></tr>", "<tr><th>Processor</th><th>Purpose</th><th>Data</th></tr>"),
    ("<td>Доставя запитването до нашата поща</td><td>Данните от формата</td>", "<td>Delivers the enquiry to our mailbox</td><td>The form data</td>"),
    ("<td>Зарежда проверката „Не съм робот“ на страницата</td><td>IP адрес и технически данни за браузъра</td>",
     "<td>Loads the “I am human” check on the page</td><td>IP address and technical browser data</td>"),
    ("<td>Intuition Machines, Inc. (hCaptcha), САЩ</td><td>Проверка „Не съм робот“</td><td>IP адрес, технически данни за браузъра и действията в него</td>",
     "<td>Intuition Machines, Inc. (hCaptcha), USA</td><td>“I am human” check</td><td>IP address, technical browser data and interactions</td>"),
    ("<td>GitHub, Inc., САЩ</td><td>Хостинг на сайта</td><td>IP адрес в техническите записи на сървъра</td>",
     "<td>GitHub, Inc., USA</td><td>Website hosting</td><td>IP address in the server’s technical logs</td>"),
    ("<td>Доставчик на имейл услугите на дружеството</td><td>Съхранение на имейлите със запитвания</td><td>Данните от формата и кореспонденцията</td>",
     "<td>The company’s email service provider</td><td>Storing enquiry emails</td><td>The form data and correspondence</td>"),
    ("Може да предоставим данни и на държавни органи, когато законът го изисква, както и на адвокати и одитори при задължение за поверителност.",
     "We may also disclose data to public authorities where the law requires it, and to lawyers and auditors bound by confidentiality."),

    # 8. Transfers
    ("<h2>8. Предаване извън Европейското икономическо пространство</h2>", "<h2>8. Transfers outside the European Economic Area</h2>"),
    ("Някои от обработващите са в САЩ или други държави извън ЕИП. Предаваме данни към тях само при наличие на една от следните гаранции:",
     "Some processors are in the USA or other countries outside the EEA. We transfer data to them only with one of the following safeguards:"),
    ("<li>решение за адекватност на Европейската комисия (чл. 45), включително Рамката за защита на данните между ЕС и САЩ, когато получателят е сертифициран по нея;</li>",
     "<li>an adequacy decision of the European Commission (Art. 45), including the EU–US Data Privacy Framework where the recipient is certified under it;</li>"),
    ("<li>стандартни договорни клаузи, одобрени от Европейската комисия (чл. 46, пар. 2, б. „в“).</li>",
     "<li>standard contractual clauses adopted by the European Commission (Art. 46(2)(c)).</li>"),
    ("При поискване ще ви предоставим информация коя гаранция се прилага за всеки получател и копие от нея.",
     "On request we will tell you which safeguard applies to each recipient and give you a copy of it."),

    # 9. Cookies
    ("<h2>9. Бисквитки и памет на браузъра</h2>", "<h2>9. Cookies and browser storage</h2>"),
    ("Сайтът не използва рекламни или аналитични бисквитки. Шрифтовете се зареждат от нашия сървър, а не от външни услуги.",
     "This website uses no advertising or analytics cookies. Fonts are loaded from our own server, not from third-party services."),
    ("Използваме само записи, които са строго необходими за изпращането на запитване и защитата от злоупотреби. За тях не се изисква съгласие (чл. 4а, ал. 2 от Закона за електронните съобщения):",
     "We only use storage that is strictly necessary for sending an enquiry and preventing abuse. No consent is required for it (Art. 4a(2) of the Bulgarian Electronic Communications Act):"),
    ("<tr><th>Запис</th><th>Кой го поставя</th><th>За какво</th><th>Срок</th></tr>", "<tr><th>Item</th><th>Set by</th><th>Purpose</th><th>Duration</th></tr>"),
    ("<td>Брой изпратени запитвания (памет на браузъра)</td><td>Сайтът</td><td>Спира масовото изпращане от едно устройство</td><td>Използва се само за последния час</td>",
     "<td>Number of enquiries sent (browser storage)</td><td>This website</td><td>Stops mass submissions from one device</td><td>Used only for the last hour</td>"),
    ("<td>Бисквитки на hCaptcha</td><td>Intuition Machines, Inc.</td><td>Разпознава автоматизирани заявки</td><td>Според политиката на hCaptcha</td>",
     "<td>hCaptcha cookies</td><td>Intuition Machines, Inc.</td><td>Detects automated requests</td><td>As set in hCaptcha’s policy</td>"),
    ("Можете да изтриете тези записи по всяко време през настройките на браузъра си. Без тях формата може да не се изпрати.",
     "You can delete these items at any time in your browser settings. Without them the form may not be sent."),

    # 10. Rights
    ("<h2>10. Вашите права</h2>", "<h2>10. Your rights</h2>"),
    ("<p>Имате право да поискате:</p>", "<p>You have the right to request:</p>"),
    ("<li>достъп до данните си и копие от тях (чл. 15);</li>", "<li>access to your data and a copy of it (Art. 15);</li>"),
    ("<li>коригиране на неточни данни (чл. 16);</li>", "<li>correction of inaccurate data (Art. 16);</li>"),
    ("<li>изтриване (чл. 17);</li>", "<li>erasure (Art. 17);</li>"),
    ("<li>ограничаване на обработването (чл. 18);</li>", "<li>restriction of processing (Art. 18);</li>"),
    ("<li>преносимост на данните, които сте ни предоставили (чл. 20).</li>", "<li>portability of the data you gave us (Art. 20).</li>"),
    ("<strong>Право на възражение (чл. 21).</strong> По всяко време можете да възразите срещу обработването, което се основава на наш легитимен интерес. Ще спрем, освен ако имаме убедителни законни основания, които преобладават над вашите интереси, или данните са нужни за правен спор.",
     "<strong>Right to object (Art. 21).</strong> You can object at any time to processing based on our legitimate interest. We will stop unless we have compelling legitimate grounds that override your interests, or the data is needed for a legal claim."),
    ("Не вземаме решения, основани изцяло на автоматизирано обработване, и не правим профилиране (чл. 22).",
     "We do not make decisions based solely on automated processing and we do not carry out profiling (Art. 22)."),
    ("<strong>Как да упражните правата си.</strong> Пишете на ", "<strong>How to exercise your rights.</strong> Write to "),
    ("</a> или на длъжностното лице по защита на данните. Отговаряме безплатно до един месец. При сложни или многобройни искания срокът може да бъде удължен с до два месеца, за което ще ви уведомим (чл. 12, пар. 3). Може да поискаме да потвърдите самоличността си, за да не предоставим данни на друг човек.",
     "</a> or to our Data Protection Officer. We reply free of charge within one month. For complex or numerous requests this can be extended by up to two months, and we will tell you if so (Art. 12(3)). We may ask you to confirm your identity so that we do not disclose data to someone else."),
    ("<strong>Жалба.</strong> Ако смятате, че правата ви са нарушени, можете да подадете жалба до Комисията за защита на личните данни: гр. София 1592, бул. „Проф. Цветан Лазаров“ № 2, ",
     "<strong>Complaints.</strong> If you believe your rights have been violated, you can complain to the Bulgarian Commission for Personal Data Protection: 2 Prof. Tsvetan Lazarov Blvd., 1592 Sofia, "),
    ("</a>. Можете да потърсите защита и пред съда (чл. 79).", "</a>. You can also seek a remedy in court (Art. 79)."),

    # 11-12
    ("<h2>11. Сигурност</h2>", "<h2>11. Security</h2>"),
    ("Сайтът работи само през защитена връзка (HTTPS). Достъпът до пощата със запитвания е ограничен до служителите, които им отговарят, и е защитен с парола. При нарушение на сигурността на данните действаме по чл. 33 и 34 от Регламента.",
     "The website runs only over a secure connection (HTTPS). Access to the enquiry mailbox is limited to the staff who answer enquiries and is password-protected. In the event of a personal data breach we act under Art. 33 and 34 of the Regulation."),
    ("<h2>12. Промени</h2>", "<h2>12. Changes</h2>"),
    ("При промяна на тази политика публикуваме новата версия на тази страница с нова дата на влизане в сила. При съществена промяна ще уведомим лицата, с които сме в активен контакт.",
     "If this policy changes, we publish the new version on this page with a new effective date. For significant changes we will inform the people we are in active contact with."),

    ("← Към началната страница", "← Back to the home page"),
    ("© 2026 СТМ „Лайф-04“ ООД", "© 2026 STM Life-04 Ltd"),
]

# language switcher: flag + code; the current language carries aria-current
FLAG_BG = ('<svg class="flag" viewBox="0 0 5 3" aria-hidden="true"><rect width="5" height="1" fill="#fff"/>'
           '<rect y="1" width="5" height="1" fill="#00966E"/><rect y="2" width="5" height="1" fill="#D62612"/></svg>')
FLAG_UK = ('<svg class="flag" viewBox="0 0 60 30" aria-hidden="true"><clipPath id="flag-uk"><path d="M30,15h30v15zv15h-30zh-30v-15zv-15h30z"/></clipPath>'
           '<path d="M0,0v30h60v-30z" fill="#012169"/><path d="M0,0L60,30M60,0L0,30" stroke="#fff" stroke-width="6"/>'
           '<path d="M0,0L60,30M60,0L0,30" clip-path="url(#flag-uk)" stroke="#C8102E" stroke-width="4"/>'
           '<path d="M30,0v30M0,15h60" stroke="#fff" stroke-width="10"/><path d="M30,0v30M0,15h60" stroke="#C8102E" stroke-width="6"/></svg>')


def switcher(bg_href, en_href, current):
    cur = ' aria-current="page"'
    return (f'<a href="{bg_href}" lang="bg"{cur if current == "bg" else ""}>{FLAG_BG}BG</a>'
            f'<a href="{en_href}" lang="en"{cur if current == "en" else ""}>{FLAG_UK}EN</a>')


PAGES = {
    "index.html": {
        "rows": T_INDEX,
        "out": "en.html",
        "switch": {lang: switcher("index.html", "en.html", lang) for lang in ("bg", "en")},
    },
    "privacy.html": {
        "rows": T_PRIVACY,
        "out": "privacy-en.html",
        "switch": {lang: switcher("privacy.html", "privacy-en.html", lang) for lang in ("bg", "en")},
    },
}

# strings that are allowed to stay Cyrillic (Bulgarian email subject and sender name)
KEEP = ("Запитване за безплатен преглед", "Сайт Лайф-04")


def build(src):
    page = PAGES[src]
    s = (SITE / src).read_text(encoding="utf8")
    missing = [row[0] for row in page["rows"] if row[0] not in s]
    if page["switch"]["bg"] not in s:
        missing.append(page["switch"]["bg"])
    if missing:
        sys.exit(f"Not found in {src}:\n  " + "\n  ".join(missing))
    s = s.replace(page["switch"]["bg"], page["switch"]["en"])
    for row in sorted(page["rows"], key=lambda r: -len(r[0])):
        s = s.replace(row[0], row[1])
    leftover = [m for m in re.findall(r"[^\n]*[А-Яа-я][^\n]*", s) if not any(k in m for k in KEEP)]
    if leftover:
        sys.exit(f"Untranslated text in {page['out']}:\n  " + "\n  ".join(x.strip() for x in leftover))
    (SITE / page["out"]).write_text(s, encoding="utf8")
    print(f"wrote website/{page['out']}")


if __name__ == "__main__":
    for src in PAGES:
        build(src)
