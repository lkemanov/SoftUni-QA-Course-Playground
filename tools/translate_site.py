"""Build the English and German pages from the Bulgarian source pages.

  website/index.html   -> en.html, de.html
  website/privacy.html -> privacy-en.html, privacy-de.html

Run after every change to a Bulgarian page:  python3 tools/translate_site.py
Each Bulgarian phrase must exist in its page; the script stops if one is
missing or if any Cyrillic text is left untranslated.
"""
import re
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent / "website"

# (Bulgarian, English, German). Longer phrases are replaced first.
T_INDEX = [
    # head, navigation, accessibility labels
    ('<html lang="bg">', '<html lang="en">', '<html lang="de">'),
    ("<title>СТМ Лайф-04 | Служба по трудова медицина</title>",
     "<title>Life-04 | Occupational Health Service</title>",
     "<title>Life-04 | Arbeitsmedizinischer Dienst</title>"),
    ("СТМ „Лайф-04“ ООД – регистрирана служба по трудова медицина от 2004 г. Оценка на риска, медицинско наблюдение, обучения и документация по ЗЗБУТ в 15 области на България.",
     "Life-04 – a registered occupational health service in Bulgaria since 2004. Risk assessment, health surveillance, training and health & safety documentation in 15 regions.",
     "Life-04 – registrierter arbeitsmedizinischer Dienst in Bulgarien seit 2004. Gefährdungsbeurteilung, arbeitsmedizinische Vorsorge, Schulungen und Arbeitsschutz-Dokumentation in 15 Regionen."),
    ('aria-label="Лайф-04 – начало"', 'aria-label="Life-04 – home"', 'aria-label="Life-04 – Startseite"'),
    ("<span>Лайф-04<small>Служба по трудова медицина</small></span>",
     "<span>Life-04<small>Occupational Health Service</small></span>",
     "<span>Life-04<small>Arbeitsmedizinischer Dienst</small></span>"),
    ('aria-label="Език"', 'aria-label="Language"', 'aria-label="Sprache"'),
    ('aria-label="Меню"', 'aria-label="Menu"', 'aria-label="Menü"'),
    ('aria-label="Надолу"', 'aria-label="Scroll down"', 'aria-label="Nach unten"'),
    ('<a href="#about">За нас</a>', '<a href="#about">About</a>', '<a href="#about">Über uns</a>'),
    ('<a href="#services">Услуги</a>', '<a href="#services">Services</a>', '<a href="#services">Leistungen</a>'),
    ('<a href="#process">Как работим</a>', '<a href="#process">How we work</a>', '<a href="#process">Ablauf</a>'),
    ('<a href="#experience">Опит</a>', '<a href="#experience">Experience</a>', '<a href="#experience">Erfahrung</a>'),
    ('<a href="#team">Екип</a>', '<a href="#team">Team</a>', '<a href="#team">Team</a>'),
    ('class="btn btn-primary">Безплатен преглед</a>', 'class="btn btn-primary">Free review</a>', 'class="btn btn-primary">Kostenloser Check</a>'),

    # hero
    ("Служба по трудова медицина · от 2004 г.", "Occupational health service · since 2004", "Arbeitsmedizinischer Dienst · seit 2004"),
    ("<h1>Над <em>20 години</em> грижа за здравето и безопасността на работещите</h1>",
     "<h1>Over <em>20 years</em> of caring for the health and safety of working people</h1>",
     "<h1>Seit über <em>20 Jahren</em> im Einsatz für Gesundheit und Sicherheit am Arbeitsplatz</h1>"),
    ("СТМ „Лайф-04“ поема цялата тема „здраве и безопасност при работа“ – от оценката на риска до медицинските прегледи и обученията. Вие се занимавате с бизнеса си, документите ви са готови за проверка във всеки момент.",
     "Life-04 takes care of everything related to health and safety at work – from risk assessment to medical check-ups and training. You run your business; your documents are ready for inspection at any time.",
     "Life-04 übernimmt das gesamte Thema Gesundheit und Sicherheit bei der Arbeit – von der Gefährdungsbeurteilung bis zu Vorsorgeuntersuchungen und Schulungen. Sie kümmern sich um Ihr Geschäft, Ihre Unterlagen sind jederzeit prüfbereit."),
    ("Безплатен преглед на документите <svg", "Free document review <svg", "Kostenlose Prüfung Ihrer Unterlagen <svg"),
    (">Вижте услугите</a>", ">See our services</a>", ">Unsere Leistungen</a>"),
    ("<span>години на пазара, без прекъсване</span>", "<span>years in the market, without interruption</span>", "<span>Jahre am Markt, ohne Unterbrechung</span>"),
    ("<span>области в България, които обслужваме на място</span>", "<span>regions in Bulgaria served on site</span>", "<span>Regionen in Bulgarien, die wir vor Ort betreuen</span>"),
    ("<span>9001 сертифицирана система за управление на качеството</span>", "<span>9001 certified quality management system</span>", "<span>9001-zertifiziertes Qualitätsmanagementsystem</span>"),

    # law
    (">Защо това е важно за вас</span>", ">Why this matters to you</span>", ">Warum das für Sie wichtig ist</span>"),
    (">Законът изисква три неща от всеки работодател</h2>", ">The law requires three things from every employer</h2>", ">Das Gesetz verlangt von jedem Arbeitgeber drei Dinge</h2>"),
    ("<h3>Оценка на риска</h3>\n        <p>За всяко работно място, с програма от мерки. Актуализира се при всяка промяна на хора, машини или помещения.</p>",
     "<h3>Risk assessment</h3>\n        <p>For every workplace, with a programme of measures. Updated whenever people, machines or premises change.</p>",
     "<h3>Gefährdungsbeurteilung</h3>\n        <p>Für jeden Arbeitsplatz, mit einem Maßnahmenprogramm. Wird bei jeder Änderung von Personal, Maschinen oder Räumen aktualisiert.</p>"),
    ("<h3>Медицинско наблюдение</h3>\n        <p>Прегледи при постъпване и периодично, заключения за годност и здравни досиета за всеки служител.</p>",
     "<h3>Health surveillance</h3>\n        <p>Pre-employment and periodic check-ups, fitness-for-work decisions and a health record for every employee.</p>",
     "<h3>Arbeitsmedizinische Vorsorge</h3>\n        <p>Einstellungs- und regelmäßige Untersuchungen, Tauglichkeitsbescheinigungen und eine Gesundheitsakte für jeden Mitarbeiter.</p>"),
    ("<h3>Обучения и инструктажи</h3>\n        <p>На ръководители, на лицата, които инструктират, и на комитета по условия на труд. Всяка година.</p>",
     "<h3>Training and briefings</h3>\n        <p>For managers, for the people who brief staff and for the working conditions committee. Every year.</p>",
     "<h3>Schulungen und Unterweisungen</h3>\n        <p>Für Führungskräfte, für die unterweisenden Personen und für den Arbeitsschutzausschuss. Jedes Jahr.</p>"),
    ("При проверка от Инспекцията по труда това са първите документи, които се искат. Липсата им води до предписания и глоби, а изготвянето им „в последния момент“ излиза по-скъпо от редовното обслужване.",
     "These are the first documents the Labour Inspectorate asks for during an inspection. Missing them leads to orders and fines, and preparing them at the last minute costs more than regular service.",
     "Bei einer Kontrolle durch die Arbeitsinspektion sind das die ersten Unterlagen, die verlangt werden. Fehlen sie, drohen Auflagen und Bußgelder – und die Erstellung in letzter Minute ist teurer als eine laufende Betreuung."),

    # about
    (">Кои сме ние</span>", ">Who we are</span>", ">Wer wir sind</span>"),
    ("<h2>Регистрирана служба по трудова медицина с над 20 години практика</h2>",
     "<h2>A registered occupational health service with over 20 years of practice</h2>",
     "<h2>Registrierter arbeitsmedizinischer Dienst mit über 20 Jahren Praxis</h2>"),
    ("Член сме на Сдружението на службите по трудова медицина в България.",
     "We are a member of the Association of Occupational Health Services in Bulgaria.",
     "Wir sind Mitglied im Verband der arbeitsmedizinischen Dienste in Bulgarien."),
    ("Управителят д-р Людмила Тенева е лекар и водещ одитор по ISO 9001, ISO 14001 и ISO 45001 с над 20 години опит. Това означава, че документите ви се изготвят от човек, който знае какво проверяват и одиторите, и Инспекцията по труда.",
     "Our managing director, Dr Lyudmila Teneva, is a physician and lead auditor for ISO 9001, ISO 14001 and ISO 45001 with over 20 years of experience. Your documents are prepared by someone who knows what both auditors and the Labour Inspectorate check.",
     "Unsere Geschäftsführerin Dr. Lyudmila Teneva ist Ärztin und leitende Auditorin für ISO 9001, ISO 14001 und ISO 45001 mit über 20 Jahren Erfahrung. Ihre Unterlagen erstellt also jemand, der weiß, worauf Auditoren und Arbeitsinspektion achten."),
    ("<span>година на пазара, без прекъсване</span>", "<span>in the market since, without interruption</span>", "<span>am Markt seit, ohne Unterbrechung</span>"),
    ("<span>сертифицирана система за управление на качеството (2015)</span>", "<span>certified quality management system (2015)</span>", "<span>zertifiziertes Qualitätsmanagementsystem (2015)</span>"),
    ("<span>удостоверение от Министерството на здравеопазването</span>", "<span>registration certificate from the Ministry of Health</span>", "<span>Registrierung beim Gesundheitsministerium</span>"),

    # benefits
    (">Какво получавате</span>", ">What you get</span>", ">Was Sie bekommen</span>"),
    (">Един партньор, който поема цялата тема „здраве и безопасност“</h2>", ">One partner for everything health and safety</h2>", ">Ein Partner für das gesamte Thema Arbeitsschutz</h2>"),
    ("<h3>Пълно нормативно съответствие</h3><p>Всички документи по Закона за здравословни и безопасни условия на труд са налични, актуални и готови за проверка във всеки момент.</p>",
     "<h3>Full legal compliance</h3><p>All documents required by the Bulgarian Health and Safety at Work Act are in place, up to date and ready for inspection at any time.</p>",
     "<h3>Volle Rechtssicherheit</h3><p>Alle Unterlagen nach dem bulgarischen Arbeitsschutzgesetz sind vorhanden, aktuell und jederzeit prüfbereit.</p>"),
    ("<h3>По-малко натоварване за екипа ви</h3><p>Ние водим документацията, прегледите и обученията. Вашият човек по безопасност има партньор, не още задачи.</p>",
     "<h3>Less workload for your team</h3><p>We handle the paperwork, check-ups and training. Your safety officer gets a partner, not more tasks.</p>",
     "<h3>Weniger Aufwand für Ihr Team</h3><p>Wir führen Dokumentation, Untersuchungen und Schulungen. Ihre Sicherheitsfachkraft bekommt einen Partner, keine zusätzlichen Aufgaben.</p>"),
    ("<h3>Оценка на риска за вашата среда</h3><p>Не общ образец, а оценка от специалисти, които вече са работили в болници, заводи, строителни обекти, офиси и училища.</p>",
     "<h3>Risk assessment for your environment</h3><p>Not a generic template, but an assessment by specialists who have already worked in hospitals, factories, construction sites, offices and schools.</p>",
     "<h3>Gefährdungsbeurteilung für Ihr Umfeld</h3><p>Keine Standardvorlage, sondern eine Beurteilung durch Fachleute, die bereits in Krankenhäusern, Fabriken, auf Baustellen, in Büros und Schulen gearbeitet haben.</p>"),
    ("<h3>По-здрави и по-защитени служители</h3><p>Годишен анализ на здравословното състояние и конкретни мерки, които намаляват отсъствията и трудовите злополуки.</p>",
     "<h3>Healthier, better protected employees</h3><p>An annual health analysis and concrete measures that reduce sick leave and workplace accidents.</p>",
     "<h3>Gesündere und besser geschützte Mitarbeiter</h3><p>Jährliche Gesundheitsanalyse und konkrete Maßnahmen, die Fehlzeiten und Arbeitsunfälle reduzieren.</p>"),

    # services
    ('<span class="eyebrow reveal">Услуги</span>', '<span class="eyebrow reveal">Services</span>', '<span class="eyebrow reveal">Leistungen</span>'),
    (">Четири области, покрити изцяло в абонамента</h2>", ">Four areas, fully covered by the subscription</h2>", ">Vier Bereiche, vollständig im Abonnement enthalten</h2>"),
    ("<use href=\"#i-search\"/></svg>Оценка на риска</button>", "<use href=\"#i-search\"/></svg>Risk assessment</button>", "<use href=\"#i-search\"/></svg>Gefährdungsbeurteilung</button>"),
    ("<use href=\"#i-pulse\"/></svg>Медицинско наблюдение</button>", "<use href=\"#i-pulse\"/></svg>Health surveillance</button>", "<use href=\"#i-pulse\"/></svg>Arbeitsmedizinische Vorsorge</button>"),
    ("<use href=\"#i-cap\"/></svg>Обучения</button>", "<use href=\"#i-cap\"/></svg>Training</button>", "<use href=\"#i-cap\"/></svg>Schulungen</button>"),
    ("<use href=\"#i-doc\"/></svg>Документация</button>", "<use href=\"#i-doc\"/></svg>Documentation</button>", "<use href=\"#i-doc\"/></svg>Dokumentation</button>"),
    ("<h3>Оценка и управление на риска</h3>", "<h3>Risk assessment and management</h3>", "<h3>Gefährdungsbeurteilung und Risikomanagement</h3>"),
    ("Програма и карти за оценка на риска", "Risk assessment programme and workplace risk cards", "Beurteilungsprogramm und Gefährdungskarten"),
    ("Оценка по Наредба № 5/1999 г.", "Assessment under Ordinance No. 5/1999", "Beurteilung nach Verordnung Nr. 5/1999"),
    ("Програма с мерки за намаляване на риска", "Programme of risk reduction measures", "Maßnahmenprogramm zur Risikominderung"),
    ("Физиологичен режим на труд и почивка", "Work and rest schedules", "Arbeits- und Pausenregelungen"),
    ('<div class="num">02</div><h3>Медицинско наблюдение</h3>', '<div class="num">02</div><h3>Health surveillance</h3>', '<div class="num">02</div><h3>Arbeitsmedizinische Vorsorge</h3>'),
    ("Годишен план за периодичните прегледи", "Annual plan for periodic check-ups", "Jahresplan für regelmäßige Untersuchungen"),
    ("Заключения за годност при постъпване", "Fitness-for-work decisions for new hires", "Tauglichkeitsbescheinigungen bei Einstellung"),
    ("Здравни досиета на всеки служител", "A health record for every employee", "Gesundheitsakte für jeden Mitarbeiter"),
    ("Годишен анализ на здравословното състояние", "Annual analysis of employee health", "Jährliche Analyse des Gesundheitszustands"),
    ('<div class="num">03</div><h3>Обучения</h3>', '<div class="num">03</div><h3>Training</h3>', '<div class="num">03</div><h3>Schulungen</h3>'),
    ("Ръководители и инструктиращи (Наредба РД-07-2)", "Managers and instructors (Ordinance RD-07-2)", "Führungskräfte und Unterweisende (Verordnung RD-07-2)"),
    ("Комитети и групи по условия на труд", "Working conditions committees and groups", "Arbeitsschutzausschüsse und -gruppen"),
    ("Длъжностни лица по Наредба № 3/1998 г.", "Designated officers under Ordinance No. 3/1998", "Beauftragte Personen nach Verordnung Nr. 3/1998"),
    ("Информиране на служителите за рисковете", "Informing employees about the risks", "Information der Mitarbeiter über die Risiken"),
    ("<h3>Документация и становища</h3>", "<h3>Documentation and expert opinions</h3>", "<h3>Dokumentation und Stellungnahmen</h3>"),
    ("Преглед и актуализация на заповедите по ЗЗБУТ", "Review and update of internal health & safety orders", "Prüfung und Aktualisierung der Arbeitsschutz-Anordnungen"),
    ("Правила и инструкции за безопасна работа", "Safe work rules and instructions", "Regeln und Anweisungen für sicheres Arbeiten"),
    ("Консултантски заключения по нормативни изисквания", "Advisory opinions on legal requirements", "Beratende Stellungnahmen zu gesetzlichen Anforderungen"),
    ("Участие при трудови злополуки и професионални заболявания", "Support with workplace accidents and occupational diseases", "Mitwirkung bei Arbeitsunfällen und Berufskrankheiten"),
    ("Пълният списък с всички услуги по Наредба № 3/2008 г. ще получите при поискване или на първата среща.",
     "The full list of services under Ordinance No. 3/2008 is available on request or at our first meeting.",
     "Die vollständige Leistungsliste nach Verordnung Nr. 3/2008 erhalten Sie auf Anfrage oder beim ersten Termin."),

    # process
    (">Как работим</span>", ">How we work</span>", ">So arbeiten wir</span>"),
    (">Пет стъпки от първата среща до постоянното обслужване</h2>", ">Five steps from the first meeting to ongoing service</h2>", ">Fünf Schritte vom ersten Treffen zur laufenden Betreuung</h2>"),
    ("<h3>Преглед на текущото състояние</h3><p>Оглед на обектите и на наличната документация. Казваме ви точно какво липсва.</p>",
     "<h3>Review of the current state</h3><p>We visit your sites and review existing documents. We tell you exactly what is missing.</p>",
     "<h3>Bestandsaufnahme</h3><p>Besichtigung Ihrer Standorte und der vorhandenen Unterlagen. Wir sagen Ihnen genau, was fehlt.</p>"),
    ("<h3>Оценка на риска</h3><p>Идентифициране на опасностите, карти за всяко работно място, програма с мерки.</p>",
     "<h3>Risk assessment</h3><p>Identifying hazards, a risk card for every workplace, a programme of measures.</p>",
     "<h3>Gefährdungsbeurteilung</h3><p>Ermittlung der Gefährdungen, Karten für jeden Arbeitsplatz, Maßnahmenprogramm.</p>"),
    ("<h3>Медицинско наблюдение</h3><p>План за прегледите, здравни досиета, заключения за годност.</p>",
     "<h3>Health surveillance</h3><p>Check-up plan, health records, fitness-for-work decisions.</p>",
     "<h3>Arbeitsmedizinische Vorsorge</h3><p>Untersuchungsplan, Gesundheitsakten, Tauglichkeitsbescheinigungen.</p>"),
    ("<h3>Обучения</h3><p>На ръководители, инструктиращи и комитет по условия на труд, с протоколи и удостоверения.</p>",
     "<h3>Training</h3><p>For managers, instructors and the working conditions committee, with minutes and certificates.</p>",
     "<h3>Schulungen</h3><p>Für Führungskräfte, Unterweisende und den Arbeitsschutzausschuss, mit Protokollen und Bescheinigungen.</p>"),
    ("<h3>Текущо обслужване</h3><p>Актуализации при промяна на хора, работни места или закони. Годишен анализ.</p>",
     "<h3>Ongoing service</h3><p>Updates whenever people, workplaces or laws change. Annual analysis.</p>",
     "<h3>Laufende Betreuung</h3><p>Aktualisierung bei Änderungen von Personal, Arbeitsplätzen oder Gesetzen. Jährliche Analyse.</p>"),
    ("<strong>Един контакт за всичко.</strong> Получавате отговорен консултант, който познава обектите ви и отговаря в рамките на работния ден.",
     "<strong>One contact for everything.</strong> You get a dedicated consultant who knows your sites and replies within the working day.",
     "<strong>Ein Ansprechpartner für alles.</strong> Sie erhalten einen festen Berater, der Ihre Standorte kennt und innerhalb eines Arbeitstages antwortet."),

    # experience
    ('<span class="eyebrow reveal">Опит</span>', '<span class="eyebrow reveal">Experience</span>', '<span class="eyebrow reveal">Erfahrung</span>'),
    (">Познаваме рисковете във вашия отрасъл, защото вече сме работили в него</h2>", ">We know the risks in your industry because we have already worked in it</h2>", ">Wir kennen die Risiken Ihrer Branche, weil wir dort bereits gearbeitet haben</h2>"),
    ("Частни и държавни организации – от трима души на дистанционна работа до болници и строителни компании с хиляди служители.",
     "Private and public organisations – from three people working remotely to hospitals and construction companies with thousands of employees.",
     "Private und öffentliche Organisationen – von drei Personen im Homeoffice bis zu Krankenhäusern und Baufirmen mit Tausenden Mitarbeitern."),
    ("</svg>Здравеопазване</div>", "</svg>Healthcare</div>", "</svg>Gesundheitswesen</div>"),
    ("</svg>Строителство</div>", "</svg>Construction</div>", "</svg>Bauwesen</div>"),
    ("</svg>Машиностроене</div>", "</svg>Mechanical engineering</div>", "</svg>Maschinenbau</div>"),
    ("</svg>Хранителна промишленост</div>", "</svg>Food industry</div>", "</svg>Lebensmittelindustrie</div>"),
    ("</svg>Образование и култура</div>", "</svg>Education and culture</div>", "</svg>Bildung und Kultur</div>"),
    ("</svg>Държавна администрация</div>", "</svg>Public administration</div>", "</svg>Öffentliche Verwaltung</div>"),
    ("</svg>Телекомуникации и IT</div>", "</svg>Telecoms and IT</div>", "</svg>Telekommunikation und IT</div>"),
    ("</svg>Търговия с горива</div>", "</svg>Fuel trading</div>", "</svg>Kraftstoffhandel</div>"),
    ("</svg>Шивашка промишленост</div>", "</svg>Garment industry</div>", "</svg>Bekleidungsindustrie</div>"),
    ("</svg>Транспорт и логистика</div>", "</svg>Transport and logistics</div>", "</svg>Transport und Logistik</div>"),
    ("</svg>Хотелиерство и ресторанти</div>", "</svg>Hotels and restaurants</div>", "</svg>Hotellerie und Gastronomie</div>"),
    ("</svg>Добив и геопроучване</div>", "</svg>Mining and geological exploration</div>", "</svg>Bergbau und geologische Erkundung</div>"),

    # clients
    (">Клиенти</span>", ">Clients</span>", ">Kunden</span>"),
    (">Доверието на международни компании и публични институции</h2>", ">Trusted by international companies and public institutions</h2>", ">Das Vertrauen internationaler Unternehmen und öffentlicher Einrichtungen</h2>"),
    ('alt="Победа"', 'alt="Pobeda"', 'alt="Pobeda"'),
    ('alt="ИАГ"', 'alt="IAG"', 'alt="IAG"'),

    # team
    (">Екип и покритие</span>", ">Team and coverage</span>", ">Team und Einsatzgebiet</span>"),
    ("<h2>Лекар, инженери и психолог – на място в 15 области</h2>", "<h2>A physician, engineers and a psychologist – on site in 15 regions</h2>", "<h2>Ärztin, Ingenieure und Psychologin – vor Ort in 15 Regionen</h2>"),
    ("<span>лекар с призната специалност по трудова медицина</span>", "<span>physician specialised in occupational medicine</span>", "<span>Fachärztin für Arbeitsmedizin</span>"),
    ("<span>инженери и технически специалисти по безопасност на труда</span>", "<span>engineers and technical specialists in occupational safety</span>", "<span>Ingenieure und Fachkräfte für Arbeitssicherheit</span>"),
    ("<span>специалист по трудова психология</span>", "<span>specialist in occupational psychology</span>", "<span>Fachkraft für Arbeitspsychologie</span>"),
    ("Съставът отговаря на Наредба № 3/2008 г. Имаме вътрешна система за обучение и информационно осигуряване на консултантите.",
     "Our team meets the requirements of Ordinance No. 3/2008. We run an internal training and knowledge system for our consultants.",
     "Die Zusammensetzung entspricht der Verordnung Nr. 3/2008. Unsere Berater werden über ein internes Schulungs- und Informationssystem fortgebildet."),
    ("<h3>Обслужвани области</h3>\n      <p>Работим на място в обектите ви.</p>",
     "<h3>Regions we serve</h3>\n      <p>We work on site at your premises.</p>",
     "<h3>Betreute Regionen</h3>\n      <p>Wir arbeiten vor Ort an Ihren Standorten.</p>"),
    ("<span>София-град</span><span>Софийска област</span><span>Пловдив</span><span>Бургас</span><span>Стара Загора</span><span>Благоевград</span><span>Хасково</span><span>Кърджали</span><span>Сливен</span><span>Плевен</span><span>Ловеч</span><span>Перник</span><span>Кюстендил</span><span>Видин</span><span>Силистра</span>",
     "<span>Sofia City</span><span>Sofia Province</span><span>Plovdiv</span><span>Burgas</span><span>Stara Zagora</span><span>Blagoevgrad</span><span>Haskovo</span><span>Kardzhali</span><span>Sliven</span><span>Pleven</span><span>Lovech</span><span>Pernik</span><span>Kyustendil</span><span>Vidin</span><span>Silistra</span>",
     "<span>Sofia-Stadt</span><span>Oblast Sofia</span><span>Plowdiw</span><span>Burgas</span><span>Stara Sagora</span><span>Blagoewgrad</span><span>Chaskowo</span><span>Kardschali</span><span>Sliwen</span><span>Plewen</span><span>Lowetsch</span><span>Pernik</span><span>Kjustendil</span><span>Widin</span><span>Silistra</span>"),
    ("<strong>Извън тези области?</strong> Работим и дистанционно за офисни екипи и хора на работа от вкъщи, а огледите на обекти се договарят отделно.",
     "<strong>Outside these regions?</strong> We also work remotely for office teams and people working from home; site visits are arranged separately.",
     "<strong>Außerhalb dieser Regionen?</strong> Für Büroteams und Mitarbeiter im Homeoffice arbeiten wir auch aus der Ferne; Besichtigungen vor Ort werden gesondert vereinbart."),

    # privacy
    (">Защита на личните данни</span>", ">Data protection</span>", ">Datenschutz</span>"),
    (">Здравните данни остават при нас. Вие получавате само заключението</h2>", ">Health data stays with us. You only receive the conclusion</h2>", ">Gesundheitsdaten bleiben bei uns. Sie erhalten nur das Ergebnis</h2>"),
    ("Здравните досиета са специална категория данни по Регламент (ЕС) 2016/679 и се съхраняват единствено от службата по трудова медицина.",
     "Health records are a special category of data under Regulation (EU) 2016/679 (GDPR) and are kept only by the occupational health service.",
     "Gesundheitsakten sind besondere Kategorien personenbezogener Daten nach Verordnung (EU) 2016/679 (DSGVO) und werden ausschließlich vom arbeitsmedizinischen Dienst aufbewahrt."),
    ("Работодателят получава заключение „годен / негоден / годен при условия“, а не диагнозите и резултатите зад него.",
     "The employer receives a conclusion – “fit / unfit / fit with conditions” – not the diagnoses and results behind it.",
     "Der Arbeitgeber erhält nur das Ergebnis „tauglich / nicht tauglich / tauglich unter Auflagen“, nicht die Diagnosen und Befunde dahinter."),
    ("Достъп до системата TM SISTEM имат само обучени служители с парола, чиито задължения го изискват.",
     "Only trained, password-protected staff whose duties require it can access the TM SISTEM software.",
     "Zugriff auf das System TM SISTEM haben nur geschulte Mitarbeiter mit Passwort, deren Aufgaben dies erfordern."),
    ("Писмени процедури за достъп, съхранение, предаване и унищожаване на здравната документация.",
     "Written procedures for accessing, storing, transferring and destroying health records.",
     "Schriftliche Verfahren für Zugriff, Aufbewahrung, Übermittlung und Vernichtung der Gesundheitsunterlagen."),
    ("<h3>Какво подписваме с вас</h3>", "<h3>What we sign with you</h3>", "<h3>Was wir mit Ihnen unterzeichnen</h3>"),
    ("</svg>Договор за трудовомедицинско обслужване</div>", "</svg>Occupational health service agreement</div>", "</svg>Vertrag über arbeitsmedizinische Betreuung</div>"),
    ("</svg>Договор за обработване на лични данни</div>", "</svg>Data processing agreement</div>", "</svg>Auftragsverarbeitungsvertrag</div>"),
    (">Какво вижда работодателят:</p>", ">What the employer sees:</p>", ">Was der Arbeitgeber sieht:</p>"),
    ('<span class="v-ok">Годен</span><span class="v-cond">Годен при условия</span><span class="v-no">Негоден</span>',
     '<span class="v-ok">Fit</span><span class="v-cond">Fit with conditions</span><span class="v-no">Unfit</span>',
     '<span class="v-ok">Tauglich</span><span class="v-cond">Tauglich unter Auflagen</span><span class="v-no">Nicht tauglich</span>'),

    # why
    (">Защо Лайф-04</span>", ">Why Life-04</span>", ">Warum Life-04</span>"),
    (">Четири неща, които ни отличават от стандартната служба</h2>", ">Four things that set us apart from a standard service</h2>", ">Vier Dinge, die uns von einem Standarddienst unterscheiden</h2>"),
    ("<h3>Ръководи ни водещ одитор по ISO 45001</h3><p>Документите ви се пишат от човек, който сам проверява такива системи. Ако имате или планирате сертификация, това спестява месеци.</p>",
     "<h3>Led by an ISO 45001 lead auditor</h3><p>Your documents are written by someone who audits such systems herself. If you have or plan a certification, this saves months.</p>",
     "<h3>Geführt von einer leitenden ISO-45001-Auditorin</h3><p>Ihre Unterlagen schreibt jemand, der solche Systeme selbst prüft. Wenn Sie eine Zertifizierung haben oder planen, spart das Monate.</p>"),
    ("<h3>Оценка на риска по отрасъл, не по шаблон</h3><p>Експлозивен прах в мелница, легионела в болнична водна система, работа на височина при монтаж. Знаем какво да търсим.</p>",
     "<h3>Industry-specific risk assessment, not a template</h3><p>Explosive dust in a mill, legionella in a hospital water system, working at height during installation. We know what to look for.</p>",
     "<h3>Branchenspezifische Beurteilung statt Schablone</h3><p>Explosionsfähiger Staub in einer Mühle, Legionellen im Wassersystem eines Krankenhauses, Arbeiten in der Höhe bei der Montage. Wir wissen, worauf wir achten müssen.</p>"),
    ("<h3>Лицензиран софтуер за здравните досиета</h3><p>Работим със специализираната система TM SISTEM, с контролиран достъп и обучени служители. Нищо не е в папки по бюрата.</p>",
     "<h3>Licensed software for health records</h3><p>We use the specialised TM SISTEM software with controlled access and trained staff. Nothing sits in folders on desks.</p>",
     "<h3>Lizenzierte Software für Gesundheitsakten</h3><p>Wir arbeiten mit dem spezialisierten System TM SISTEM, mit kontrolliertem Zugriff und geschulten Mitarbeitern. Nichts liegt in Ordnern auf dem Schreibtisch.</p>"),
    ("<h3>Същият екип от 2004 г. насам</h3><p>Пряк контакт с управителя. Клиенти, с които работим над десет години, са нормата, а не изключение.</p>",
     "<h3>The same team since 2004</h3><p>Direct contact with the managing director. Clients who have worked with us for over ten years are the norm, not the exception.</p>",
     "<h3>Dasselbe Team seit 2004</h3><p>Direkter Kontakt zur Geschäftsführerin. Kunden, die seit über zehn Jahren bei uns sind, sind die Regel, nicht die Ausnahme.</p>"),

    # next steps
    (">Следващи стъпки</span>", ">Next steps</span>", ">Nächste Schritte</span>"),
    (">Три стъпки до подписан договор</h2>", ">Three steps to a signed contract</h2>", ">In drei Schritten zum Vertrag</h2>"),
    ("<h3>Разговор от 20 минути</h3><p>Брой служители, обекти, какво имате към момента. По телефон или на място.</p>",
     "<h3>A 20-minute call</h3><p>Number of employees, sites, what you already have. By phone or in person.</p>",
     "<h3>20-minütiges Gespräch</h3><p>Mitarbeiterzahl, Standorte, was Sie bereits haben. Telefonisch oder vor Ort.</p>"),
    ('<span class="tag">Безплатно</span>', '<span class="tag">Free</span>', '<span class="tag">Kostenlos</span>'),
    ("<h3>Преглед на документите</h3><p>Казваме ви какво липсва и какво би отбелязала Инспекцията по труда. Получавате това независимо дали подпишете с нас.</p>",
     "<h3>Document review</h3><p>We tell you what is missing and what the Labour Inspectorate would flag. You keep this whether or not you sign with us.</p>",
     "<h3>Prüfung der Unterlagen</h3><p>Wir sagen Ihnen, was fehlt und was die Arbeitsinspektion beanstanden würde. Das gehört Ihnen, auch wenn Sie nicht bei uns unterschreiben.</p>"),
    ("<h3>Оферта и договор</h3><p>Индивидуална оферта до 3 работни дни. При съгласие започваме в седмицата след подписване.</p>",
     "<h3>Offer and contract</h3><p>A tailored offer within 3 working days. Once agreed, we start the week after signing.</p>",
     "<h3>Angebot und Vertrag</h3><p>Individuelles Angebot innerhalb von 3 Arbeitstagen. Nach Zusage starten wir in der Woche nach der Unterzeichnung.</p>"),
    ("Предстои ви проверка или смяна на досегашната служба? <strong>", "Facing an inspection or switching from your current provider? <strong>", "Steht eine Kontrolle an oder wechseln Sie Ihren bisherigen Dienst? <strong>"),
    (">Поемаме и текущи случаи с кратък срок.</strong>", ">We also take on urgent cases at short notice.</strong>", ">Wir übernehmen auch dringende Fälle kurzfristig.</strong>"),

    # contact
    (">За контакт</span>", ">Contact</span>", ">Kontakt</span>"),
    ("<h2>Свържете се с нас</h2>", "<h2>Get in touch</h2>", "<h2>Nehmen Sie Kontakt auf</h2>"),
    ('<div class="avatar">ЛТ</div>', '<div class="avatar">LT</div>', '<div class="avatar">LT</div>'),
    ("<b>Д-р Людмила Тенева</b><span>Управител, лекар по трудова медицина</span>",
     "<b>Dr Lyudmila Teneva</b><span>Managing director, occupational health physician</span>",
     "<b>Dr. Lyudmila Teneva</b><span>Geschäftsführerin, Fachärztin für Arbeitsmedizin</span>"),
    ("София 1309, ул. „Зайчар“ № 125, офис 2", "125 Zaychar St., office 2, 1309 Sofia, Bulgaria", "ul. Zaychar 125, Büro 2, 1309 Sofia, Bulgarien"),
    ("<h3>Изпрати запитване</h3>", "<h3>Send an enquiry</h3>", "<h3>Anfrage senden</h3>"),
    ('<label>Име<input name="Име"', '<label>Name<input name="Name"', '<label>Name<input name="Name"'),
    ('<span>Фирма <span class="req"', '<span>Company <span class="req"', '<span>Firma <span class="req"'),
    ('<input name="Фирма"', '<input name="Company"', '<input name="Firma"'),
    ('<span>Телефон <span class="req"', '<span>Phone <span class="req"', '<span>Telefon <span class="req"'),
    ('<input name="Телефон"', '<input name="Phone"', '<input name="Telefon"'),
    ('title="Само цифри, интервали и +"', 'title="Digits, spaces and + only"', 'title="Nur Ziffern, Leerzeichen und +"'),
    ('<span>Имейл <span class="req"', '<span>Email <span class="req"', '<span>E-Mail <span class="req"'),
    ("'Моля, въведете валиден телефонен номер.'", "'Please enter a valid phone number.'", "'Bitte geben Sie eine gültige Telefonnummer ein.'"),
    ('<label>Брой служители\n        <select name="Брой служители">', '<label>Number of employees\n        <select name="Employees">', '<label>Anzahl Mitarbeiter\n        <select name="Mitarbeiter">'),
    ("<option>до 10</option><option>11 – 50</option><option>51 – 250</option><option>над 250</option>",
     "<option>up to 10</option><option>11 – 50</option><option>51 – 250</option><option>over 250</option>",
     "<option>bis 10</option><option>11 – 50</option><option>51 – 250</option><option>über 250</option>"),
    ('<label>Съобщение<textarea name="Съобщение"', '<label>Message<textarea name="Message"', '<label>Nachricht<textarea name="Nachricht"'),
    ('placeholder="Обекти, дейност, предстояща проверка…"', 'placeholder="Sites, line of business, upcoming inspection…"', 'placeholder="Standorte, Tätigkeit, anstehende Kontrolle…"'),
    ('data-hl="bg"', 'data-hl="en"', 'data-hl="de"'),
    (">Изпратете запитване <svg", ">Send enquiry <svg", ">Anfrage senden <svg"),
    ("Запитването се изпраща директно до office@life-04.com. Ще се свържем с вас в рамките на 2 работни дни.",
     "Your enquiry goes straight to office@life-04.com. We will get back to you within 2 working days.",
     "Ihre Anfrage geht direkt an office@life-04.com. Wir melden uns innerhalb von 2 Arbeitstagen."),

    # consent and footer
    ('href="privacy.html"', 'href="privacy-en.html"', 'href="privacy-de.html"'),
    ("<span>Запознах се с <a", "<span>I have read the <a", "<span>Ich habe die <a"),
    (">Политиката за поверителност</a> и знам как ще бъдат използвани данните ми.</span>",
     ">Privacy Policy</a> and know how my data will be used.</span>",
     ">Datenschutzerklärung</a> gelesen und weiß, wie meine Daten verwendet werden.</span>"),
    ("СТМ „Лайф-04“ ООД · ЕИК 123673206 · София 1309, ул. „Зайчар“ № 125 · Удостоверение № 052-3 от МЗ",
     "STM Life-04 Ltd · Company ID (EIK) 123673206 · 125 Zaychar St., 1309 Sofia, Bulgaria · Ministry of Health registration No. 052-3",
     "STM Life-04 OOD · Firmennummer (EIK) 123673206 · ul. Zaychar 125, 1309 Sofia, Bulgarien · Registrierung Gesundheitsministerium Nr. 052-3"),
    (">Политика за поверителност</a><a", ">Privacy Policy</a><a", ">Datenschutz</a><a"),

    # form messages (script)
    ("' Можете да пишете и на office@life-04.com или да се обадите на +359 897 932 200.'",
     "' You can also email office@life-04.com or call +359 897 932 200.'",
     "' Sie können auch an office@life-04.com schreiben oder +359 897 932 200 anrufen.'"),
    ("'Благодарим! Запитването е изпратено. Ще се свържем с вас в рамките на 2 работни дни.'",
     "'Thank you! Your enquiry has been sent. We will get back to you within 2 working days.'",
     "'Vielen Dank! Ihre Anfrage wurde gesendet. Wir melden uns innerhalb von 2 Arbeitstagen.'"),
    ("'Благодарим! Запитването е изпратено.'", "'Thank you! Your enquiry has been sent.'", "'Vielen Dank! Ihre Anfrage wurde gesendet.'"),
    ("'Моля, проверете данните и натиснете бутона отново.'", "'Please check your details and press the button again.'", "'Bitte prüfen Sie Ihre Angaben und klicken Sie erneut.'"),
    ("'Запитването ви вече е изпратено. Моля, изчакайте минута преди да изпратите ново.'",
     "'Your enquiry has already been sent. Please wait a minute before sending another one.'",
     "'Ihre Anfrage wurde bereits gesendet. Bitte warten Sie eine Minute, bevor Sie eine neue senden.'"),
    ("'Достигнат е лимитът от запитвания за един час.'", "'You have reached the limit of enquiries for this hour.'", "'Das Limit an Anfragen für diese Stunde ist erreicht.'"),
    ("'Моля, премахнете връзките (линковете) от съобщението.'", "'Please remove the links from your message.'", "'Bitte entfernen Sie die Links aus Ihrer Nachricht.'"),
    ("'Моля, потвърдете, че не сте робот.'", "'Please confirm that you are not a robot.'", "'Bitte bestätigen Sie, dass Sie kein Roboter sind.'"),
    ("'Запитването не можа да бъде изпратено.'", "'Your enquiry could not be sent.'", "'Ihre Anfrage konnte nicht gesendet werden.'"),
    ("send.textContent='Изпращане…'", "send.textContent='Sending…'", "send.textContent='Wird gesendet…'"),
    # the office reads Bulgarian: keep the email subject in Bulgarian, marked with the page language
    ("'Запитване за безплатен преглед – '", "'Запитване за безплатен преглед (EN) – '", "'Запитване за безплатен преглед (DE) – '"),
]

T_PRIVACY = [
    ('<html lang="bg">', '<html lang="en">', '<html lang="de">'),
    ("<title>Политика за поверителност | СТМ Лайф-04</title>", "<title>Privacy Policy | Life-04</title>", "<title>Datenschutzerklärung | Life-04</title>"),
    ("Как СТМ „Лайф-04“ ООД обработва личните данни, изпратени чрез сайта.",
     "How STM Life-04 Ltd processes personal data sent through this website.",
     "Wie die STM Life-04 OOD personenbezogene Daten verarbeitet, die über diese Website gesendet werden."),
    ('href="index.html"', 'href="en.html"', 'href="de.html"'),
    ("</svg></span>Лайф-04</a>", "</svg></span>Life-04</a>", "</svg></span>Life-04</a>"),
    ('aria-label="Език"', 'aria-label="Language"', 'aria-label="Sprache"'),
    ("<h1>Политика за поверителност</h1>", "<h1>Privacy Policy</h1>", "<h1>Datenschutzerklärung</h1>"),
    ("В сила от 26 октомври 2026 г.", "Effective from 26 October 2026", "Gültig ab 26. Oktober 2026"),
    ("Тази политика обяснява какви лични данни събираме чрез сайта, защо и как ги пазим. Тя се отнася само до сайта и формата за запитване. Здравните данни на служителите на нашите клиенти се обработват по отделни правила, уговорени в договора за трудовомедицинско обслужване.",
     "This policy explains what personal data we collect through this website, why, and how we protect it. It covers only the website and the enquiry form. Health data of our clients’ employees is processed under separate rules agreed in the occupational health service contract.",
     "Diese Erklärung beschreibt, welche personenbezogenen Daten wir über die Website erheben, warum und wie wir sie schützen. Sie gilt nur für die Website und das Anfrageformular. Gesundheitsdaten der Mitarbeiter unserer Kunden werden nach gesonderten Regeln verarbeitet, die im Vertrag über die arbeitsmedizinische Betreuung vereinbart sind."),
    ("<h2>1. Кой отговаря за данните</h2>", "<h2>1. Who is responsible for your data</h2>", "<h2>1. Verantwortlicher</h2>"),
    ("СТМ „Лайф-04“ ООД, ЕИК 123673206, адрес: София 1309, ул. „Зайчар“ № 125, офис 2. Имейл:",
     "STM Life-04 Ltd, company ID (EIK) 123673206, address: 125 Zaychar St., office 2, 1309 Sofia, Bulgaria. Email:",
     "STM Life-04 OOD, Firmennummer (EIK) 123673206, Anschrift: ul. Zaychar 125, Büro 2, 1309 Sofia, Bulgarien. E-Mail:"),
    (", телефон: +359 897 932 200.", ", phone: +359 897 932 200.", ", Telefon: +359 897 932 200."),
    ("<h2>2. Какви данни събираме</h2>", "<h2>2. What data we collect</h2>", "<h2>2. Welche Daten wir erheben</h2>"),
    ("Когато изпратите запитване, получаваме данните, които сами въведете във формата:",
     "When you send an enquiry, we receive the data you enter in the form:",
     "Wenn Sie eine Anfrage senden, erhalten wir die Daten, die Sie im Formular eingeben:"),
    ("<li>име, фирма, телефон и имейл;</li>", "<li>name, company, phone and email;</li>", "<li>Name, Firma, Telefon und E-Mail;</li>"),
    ("<li>брой служители и текста на съобщението.</li>", "<li>number of employees and the text of your message.</li>", "<li>Mitarbeiterzahl und den Text Ihrer Nachricht.</li>"),
    ("Моля, не изпращайте чрез формата здравна информация за себе си или за служители. Тя не е нужна за запитването.",
     "Please do not send health information about yourself or your employees through the form. It is not needed for an enquiry.",
     "Bitte senden Sie über das Formular keine Gesundheitsinformationen über sich oder Ihre Mitarbeiter. Für eine Anfrage sind sie nicht erforderlich."),
    ("<h2>3. Защо ги използваме и на какво основание</h2>", "<h2>3. Why we use it and on what legal basis</h2>", "<h2>3. Zweck und Rechtsgrundlage</h2>"),
    ("Използваме данните само за да отговорим на запитването ви, да подготвим оферта и, ако решите, да сключим договор. Основанието е предприемане на стъпки преди сключване на договор по ваше искане (чл. 6, пар. 1, буква „б“ от Общия регламент за защита на данните, Регламент (ЕС) 2016/679). Не използваме данните за реклама и не ги продаваме.",
     "We use the data only to answer your enquiry, prepare an offer and, if you wish, conclude a contract. The legal basis is taking steps at your request before entering into a contract (Art. 6(1)(b) of the General Data Protection Regulation, Regulation (EU) 2016/679). We do not use the data for advertising and we do not sell it.",
     "Wir verwenden die Daten nur, um Ihre Anfrage zu beantworten, ein Angebot zu erstellen und, wenn Sie es wünschen, einen Vertrag abzuschließen. Rechtsgrundlage ist die Durchführung vorvertraglicher Maßnahmen auf Ihre Anfrage (Art. 6 Abs. 1 lit. b der Datenschutz-Grundverordnung, Verordnung (EU) 2016/679). Wir nutzen die Daten nicht für Werbung und verkaufen sie nicht."),
    ("<h2>4. Колко време ги пазим</h2>", "<h2>4. How long we keep it</h2>", "<h2>4. Speicherdauer</h2>"),
    ("Ако не сключим договор, изтриваме запитването до 12 месеца след последния ни контакт. Ако сключим договор, данните стават част от договорната документация и се пазят толкова, колкото изисква законът.",
     "If no contract follows, we delete the enquiry within 12 months of our last contact. If we sign a contract, the data becomes part of the contract records and is kept for as long as the law requires.",
     "Kommt kein Vertrag zustande, löschen wir die Anfrage spätestens 12 Monate nach dem letzten Kontakt. Kommt ein Vertrag zustande, werden die Daten Teil der Vertragsunterlagen und so lange aufbewahrt, wie es das Gesetz verlangt."),
    ("<h2>5. Кой друг ги вижда</h2>", "<h2>5. Who else sees it</h2>", "<h2>5. Empfänger</h2>"),
    ("За да работи сайтът, ползваме следните доставчици. Те обработват данни само от наше име:",
     "To run the website we use the following providers. They process data only on our behalf:",
     "Für den Betrieb der Website nutzen wir folgende Dienstleister. Sie verarbeiten Daten nur in unserem Auftrag:"),
    ("<tr><th>Доставчик</th><th>За какво</th><th>Какви данни</th></tr>", "<tr><th>Provider</th><th>Purpose</th><th>Data</th></tr>", "<tr><th>Anbieter</th><th>Zweck</th><th>Daten</th></tr>"),
    ("<td>Доставят запитването до нашата поща</td><td>Данните от формата</td>", "<td>Deliver the enquiry to our mailbox</td><td>The form data</td>", "<td>Zustellung der Anfrage an unser Postfach</td><td>Die Formulardaten</td>"),
    ("<td>Проверка „Не съм робот“ срещу спам</td><td>Технически данни за браузъра и IP адрес</td>", "<td>“I am human” check against spam</td><td>Technical browser data and IP address</td>", "<td>„Ich bin kein Roboter“-Prüfung gegen Spam</td><td>Technische Browserdaten und IP-Adresse</td>"),
    ("<td>Хостинг на сайта</td><td>IP адрес в техническите записи на сървъра</td>", "<td>Website hosting</td><td>IP address in the server’s technical logs</td>", "<td>Hosting der Website</td><td>IP-Adresse in den technischen Server-Protokollen</td>"),
    ("Някои от тези доставчици са в САЩ. Предаването на данни става въз основа на Рамката за защита на данните между ЕС и САЩ или стандартни договорни клаузи на Европейската комисия.",
     "Some of these providers are based in the USA. Transfers take place under the EU–US Data Privacy Framework or the European Commission’s standard contractual clauses.",
     "Einige dieser Anbieter haben ihren Sitz in den USA. Die Übermittlung erfolgt auf Grundlage des EU-US-Datenschutzrahmens oder der Standardvertragsklauseln der Europäischen Kommission."),
    ("<h2>6. Бисквитки и памет на браузъра</h2>", "<h2>6. Cookies and browser storage</h2>", "<h2>6. Cookies und Browserspeicher</h2>"),
    ("Сайтът не използва рекламни или аналитични бисквитки. Шрифтовете се зареждат от нашия сървър, а не от външни услуги. Браузърът ви пази само броя изпратени запитвания за последния час, за да спрем масовото изпращане. Тази информация не напуска устройството ви. Проверката hCaptcha може да постави собствени бисквитки, необходими за защитата от ботове.",
     "This website uses no advertising or analytics cookies. Fonts are loaded from our own server, not from third-party services. Your browser only stores how many enquiries were sent in the last hour, so we can stop mass submissions; this never leaves your device. The hCaptcha check may set its own cookies needed for bot protection.",
     "Diese Website verwendet keine Werbe- oder Analyse-Cookies. Schriftarten werden von unserem eigenen Server geladen, nicht von Drittanbietern. Ihr Browser speichert nur, wie viele Anfragen in der letzten Stunde gesendet wurden, um Massensendungen zu verhindern; diese Information verlässt Ihr Gerät nicht. Die hCaptcha-Prüfung kann eigene, für den Schutz vor Bots notwendige Cookies setzen."),
    ("<h2>7. Вашите права</h2>", "<h2>7. Your rights</h2>", "<h2>7. Ihre Rechte</h2>"),
    ("Имате право да поискате достъп до данните си, тяхната поправка или изтриване, ограничаване на обработването, преносимост, както и да възразите срещу обработването. Пишете ни на",
     "You have the right to access, correct or delete your data, to restrict processing, to data portability and to object to processing. Write to us at",
     "Sie haben das Recht auf Auskunft, Berichtigung, Löschung, Einschränkung der Verarbeitung, Datenübertragbarkeit und Widerspruch. Schreiben Sie uns an"),
    (". Отговаряме до един месец.", ". We reply within one month.", ". Wir antworten innerhalb eines Monats."),
    ("Ако смятате, че правата ви са нарушени, можете да подадете жалба до Комисията за защита на личните данни: София 1592, бул. „Проф. Цветан Лазаров“ № 2,",
     "If you believe your rights have been violated, you can complain to the Bulgarian Commission for Personal Data Protection: 2 Prof. Tsvetan Lazarov Blvd., 1592 Sofia,",
     "Wenn Sie der Ansicht sind, dass Ihre Rechte verletzt wurden, können Sie sich bei der bulgarischen Datenschutzkommission beschweren: Bul. Prof. Tsvetan Lazarov 2, 1592 Sofia,"),
    ("<h2>8. Промени</h2>", "<h2>8. Changes</h2>", "<h2>8. Änderungen</h2>"),
    ("При промяна на тази политика ще публикуваме новата версия на тази страница с нова дата.",
     "If this policy changes, we will publish the new version on this page with a new date.",
     "Bei Änderungen veröffentlichen wir die neue Fassung auf dieser Seite mit neuem Datum."),
    ("← Към началната страница", "← Back to the home page", "← Zur Startseite"),
    ("© 2026 СТМ „Лайф-04“ ООД", "© 2026 STM Life-04 Ltd", "© 2026 STM Life-04 OOD"),
]

PAGES = {
    "index.html": {
        "rows": T_INDEX,
        "out": {"en": "en.html", "de": "de.html"},
        "switch": {
            "bg": '<a href="index.html" lang="bg" aria-current="page">BG</a><a href="en.html" lang="en">EN</a><a href="de.html" lang="de">DE</a>',
            "en": '<a href="index.html" lang="bg">BG</a><a href="en.html" lang="en" aria-current="page">EN</a><a href="de.html" lang="de">DE</a>',
            "de": '<a href="index.html" lang="bg">BG</a><a href="en.html" lang="en">EN</a><a href="de.html" lang="de" aria-current="page">DE</a>',
        },
    },
    "privacy.html": {
        "rows": T_PRIVACY,
        "out": {"en": "privacy-en.html", "de": "privacy-de.html"},
        "switch": {
            "bg": '<a href="privacy.html" lang="bg" aria-current="page">BG</a><a href="privacy-en.html" lang="en">EN</a><a href="privacy-de.html" lang="de">DE</a>',
            "en": '<a href="privacy.html" lang="bg">BG</a><a href="privacy-en.html" lang="en" aria-current="page">EN</a><a href="privacy-de.html" lang="de">DE</a>',
            "de": '<a href="privacy.html" lang="bg">BG</a><a href="privacy-en.html" lang="en">EN</a><a href="privacy-de.html" lang="de" aria-current="page">DE</a>',
        },
    },
}

# strings that are allowed to stay Cyrillic (Bulgarian email subject and sender name)
KEEP = ("Запитване за безплатен преглед", "Сайт Лайф-04")


def build(src, lang):
    page = PAGES[src]
    s = (SITE / src).read_text(encoding="utf8")
    col = {"en": 1, "de": 2}[lang]
    missing = [row[0] for row in page["rows"] if row[0] not in s]
    if page["switch"]["bg"] not in s:
        missing.append(page["switch"]["bg"])
    if missing:
        sys.exit(f"Not found in {src}:\n  " + "\n  ".join(missing))
    s = s.replace(page["switch"]["bg"], page["switch"][lang])
    for row in sorted(page["rows"], key=lambda r: -len(r[0])):
        s = s.replace(row[0], row[col])
    leftover = [m for m in re.findall(r"[^\n]*[А-Яа-я][^\n]*", s) if not any(k in m for k in KEEP)]
    if leftover:
        sys.exit(f"Untranslated text in {page['out'][lang]}:\n  " + "\n  ".join(x.strip() for x in leftover))
    (SITE / page["out"][lang]).write_text(s, encoding="utf8")
    print(f"wrote website/{page['out'][lang]}")


if __name__ == "__main__":
    for src in PAGES:
        for lang in ("en", "de"):
            build(src, lang)
