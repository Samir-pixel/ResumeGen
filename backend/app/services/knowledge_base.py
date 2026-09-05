"""Доменные паттерны и технологический каталог для генерации реалистичных резюме."""
from __future__ import annotations

# ─── ДОМЕНЫ ────────────────────────────────────────────────────────────────────

DOMAIN_PATTERNS: dict[str, dict] = {
    "FinTech": {
        "keywords": ["payment", "bank", "loan", "finance", "fintech", "scoring",
                     "billing", "lending", "kyc", "transaction", "wallet"],
        "products": [
            "loan origination and approval platform",
            "payment reconciliation and settlement service",
            "SME financing automation system",
            "digital banking operations portal",
            "client scoring and risk assessment module",
            "invoice processing and factoring platform",
        ],
        "integrations": ["payment gateway", "KYC provider", "accounting system",
                         "credit bureau API", "SWIFT gateway", "open banking API"],
        "problems": ["manual approval queues", "slow reconciliation", "audit traceability",
                     "fraud detection latency", "multi-currency handling", "regulatory reporting"],
        # Реальные компании: mid-tier FinTech / embedded banking / payments
        "company_names": [
            "Mambu", "Railsr", "Funding Circle", "OpenPayd", "Yapily",
            "Currencycloud", "Tink", "Nium", "Payoneer", "Paysafe",
            "OakNorth", "Float", "Paidy", "TrueLayer", "Modulr",
        ],
        "sectors": ["FinTech", "Banking", "Digital Lending", "Payments"],
    },
    "E-commerce": {
        "keywords": ["marketplace", "e-commerce", "catalog", "order", "checkout",
                     "retail", "seller", "product", "cart", "shop"],
        "products": [
            "order management and fulfillment platform",
            "seller operations and onboarding portal",
            "product catalog and search service",
            "customer loyalty and promotions engine",
            "multi-warehouse inventory management system",
            "returns and refunds processing service",
        ],
        "integrations": ["warehouse management system", "payment provider",
                         "delivery API", "ERP", "recommendation engine", "PIM system"],
        "problems": ["inventory sync delays", "checkout failures", "manual seller moderation",
                     "slow search indexing", "order status inconsistency", "high return rate"],
        # Реальные компании: e-commerce, marketplace, logistics tech
        "company_names": [
            "Vinted", "OLX Group", "Joom", "Lamoda", "Syte",
            "Mirakl", "Tradebyte", "Akeneo", "Omnivore", "Fabric",
            "Inpost", "Wolt", "Bolt Food", "Packlink", "Stuart",
        ],
        "sectors": ["E-commerce", "Retail Tech", "Marketplace"],
    },
    "SaaS": {
        "keywords": ["saas", "subscription", "crm", "workflow", "analytics",
                     "platform", "b2b", "automation", "dashboard", "tenant"],
        "products": [
            "workflow automation and task management platform",
            "customer operations and support portal",
            "multi-tenant SaaS analytics dashboard",
            "B2B subscription management service",
            "internal operations and reporting tool",
            "document management and approval workflow",
        ],
        "integrations": ["CRM", "email provider", "billing service",
                         "Slack", "SSO provider", "webhook manager"],
        "problems": ["slow reporting", "manual onboarding", "tenant data isolation",
                     "audit log gaps", "role-based access complexity", "notification reliability"],
        # Реальные компании: B2B SaaS, productivity, dev tools
        "company_names": [
            "Pipedrive", "Typeform", "Personio", "Pipefy", "Front",
            "Retool", "Airtable", "Xero", "Loom", "Paddle",
            "Chargebee", "Freshworks", "Intercom", "Linear", "Notion",
        ],
        "sectors": ["SaaS", "B2B Software", "Productivity Tools"],
    },
    "Logistics": {
        "keywords": ["logistics", "shipment", "warehouse", "route", "delivery",
                     "fleet", "cargo", "freight", "tracking", "dispatch"],
        "products": [
            "shipment tracking and status notification service",
            "warehouse operations and slot management platform",
            "last-mile delivery route optimization system",
            "carrier integration and freight booking portal",
            "fleet management and driver assignment module",
            "cross-border customs documentation service",
        ],
        "integrations": ["carrier API", "GPS provider", "ERP", "customs API",
                         "warehouse management system", "mobile driver app"],
        "problems": ["late status updates", "route planning overhead", "warehouse bottlenecks",
                     "carrier API instability", "manual dispatch coordination", "POD processing delays"],
        # Реальные компании: logistics tech, supply chain
        "company_names": [
            "Sennder", "FreightHub", "Forto", "Hive", "Packlink",
            "Stuart", "Bringg", "Project44", "FourKites", "Convoy",
            "Logiwa", "Flexport", "Stord", "ShipBob", "Shipstation",
        ],
        "sectors": ["Logistics Tech", "Supply Chain", "Last-Mile Delivery"],
    },
    "Healthcare": {
        "keywords": ["health", "clinic", "patient", "appointment", "medical",
                     "hospital", "ehr", "telemedicine", "pharmacy", "lab"],
        "products": [
            "appointment scheduling and patient communication platform",
            "clinical workflow and EHR integration service",
            "patient portal with medical history access",
            "lab results delivery and notification system",
            "healthcare provider network management platform",
            "insurance claim processing automation service",
        ],
        "integrations": ["EHR", "SMS provider", "insurance gateway",
                         "lab information system", "pharmacy API", "video call provider"],
        "problems": ["manual appointment handling", "fragmented patient history",
                     "reporting delays", "missed follow-up notifications",
                     "insurance claim rejections", "staff schedule conflicts"],
        # Реальные компании: digital health, telehealth
        "company_names": [
            "Doctolib", "Kry", "Alan", "Medbelle", "Babylon Health",
            "Sword Health", "Hims & Hers", "Livi", "Teladoc", "Nuvei Health",
            "Instacare", "Zocdoc", "CareMount", "HealthHero", "Healios",
        ],
        "sectors": ["HealthTech", "Digital Health", "Clinical Operations"],
    },
    "ERP": {
        "keywords": ["erp", "supply", "manufacturing", "inventory", "procurement",
                     "1c", "accounting", "enterprise", "production", "mrp"],
        "products": [
            "ERP module for procurement and supplier management",
            "production planning and manufacturing execution system",
            "inventory control and warehouse operations module",
            "financial consolidation and reporting service",
            "HR and payroll management module",
            "asset tracking and maintenance planning system",
        ],
        "integrations": ["1C", "warehouse system", "document storage",
                         "bank statement import", "EDI provider", "BI platform"],
        "problems": ["manual approval flows", "duplicated records",
                     "slow operational reports", "data sync between modules",
                     "multi-entity accounting", "legacy system migration"],
        # Реальные компании: enterprise/ERP software vendors
        "company_names": [
            "Epicor", "Infor", "IFS", "Unit4", "Sage Group",
            "Acumatica", "Syspro", "Aptean", "Plex Systems", "Rootstock",
            "Priority Software", "Kinetic", "MYOB", "Brightpearl", "Katana",
        ],
        "sectors": ["Enterprise Software", "ERP", "Manufacturing Tech"],
    },
    "EdTech": {
        "keywords": ["education", "edtech", "learning", "course", "lms",
                     "student", "teacher", "training", "e-learning", "skill"],
        "products": [
            "online learning platform with course management",
            "corporate training and certification system",
            "adaptive learning and progress tracking service",
            "live session and webinar management platform",
            "skills assessment and quiz engine",
            "learning content management system",
        ],
        "integrations": ["video streaming provider", "payment gateway",
                         "SSO", "certificate authority", "Zoom API", "content CDN"],
        "problems": ["video streaming reliability", "progress tracking accuracy",
                     "content delivery latency", "certificate fraud prevention",
                     "large concurrent session handling", "offline access sync"],
        # Реальные компании: e-learning, edtech
        "company_names": [
            "Preply", "Lingoda", "Teachable", "Thinkific", "Learnworlds",
            "Kahoot", "Quizlet", "Duolingo", "Stepik", "GetCourse",
            "Talent LMS", "Docebo", "Absorb LMS", "360Learning", "Moodle HQ",
        ],
        "sectors": ["EdTech", "E-Learning", "Corporate Training"],
    },
    "iGaming": {
        "keywords": ["igaming", "casino", "betting", "sports", "gambling",
                     "game", "player", "bonus", "jackpot", "slot"],
        "products": [
            "player account management and KYC platform",
            "bonus and promotion engine for gaming operators",
            "real-time odds and sports betting service",
            "payment processing and withdrawal management system",
            "anti-fraud and responsible gaming monitoring service",
            "game integration and aggregation platform",
        ],
        "integrations": ["payment provider", "KYC API", "game provider",
                         "odds feed", "fraud detection service", "affiliate tracking"],
        "problems": ["bonus abuse", "payment fraud", "regulatory compliance",
                     "player churn", "high-concurrency event handling",
                     "geo-blocking enforcement"],
        # Реальные компании: iGaming / sports betting / B2B gaming
        "company_names": [
            "Sportradar", "GiG (Gaming Innovation Group)", "Kindred Group",
            "Betsson", "Betway", "Pinnacle", "Parimatch", "Kambi",
            "OpenBet", "SBTech", "Amelco", "Altenar", "BetConstruct",
            "EveryMatrix", "Soft2Bet",
        ],
        "sectors": ["iGaming", "Online Gambling", "Sports Betting"],
    },
    "Telecom": {
        "keywords": ["telecom", "telco", "mobile", "network", "operator",
                     "billing", "subscriber", "voip", "carrier", "mvno"],
        "products": [
            "subscriber billing and tariff management system",
            "network event processing and CDR handling platform",
            "self-service customer portal for mobile subscribers",
            "MVNO operations and provisioning service",
            "roaming data exchange and settlement platform",
            "SIM card lifecycle management system",
        ],
        "integrations": ["network element", "CRM", "rating engine",
                         "payment gateway", "regulatory reporting API", "SMS gateway"],
        "problems": ["billing discrepancies", "CDR processing delays",
                     "customer churn prediction", "network congestion events",
                     "multi-tariff rating complexity", "high-volume data ingestion"],
        # Реальные компании: telecom software vendors / BSS / OSS
        "company_names": [
            "Amdocs", "Comverse", "Netcracker", "Subex", "Alepo",
            "CSG Systems", "Optiva", "TELARIX", "MATRIXX", "FICO Tonbeller",
            "Evolvent", "Openwave", "Guavus", "Comptel", "Sigma Systems",
        ],
        "sectors": ["Telecom", "Mobile Networks", "MVNO"],
    },
}

DEFAULT_DOMAIN = "SaaS"

# ─── ТЕХНОЛОГИЧЕСКИЙ КАТАЛОГ ────────────────────────────────────────────────────

TECH_CATALOG: dict[str, dict] = {
    # Languages
    "Python": {"category": "language", "use": "backend services and automation",
               "related": ["FastAPI", "Django", "Celery", "Pytest"]},
    # Frameworks
    "FastAPI": {"category": "framework", "use": "typed async APIs",
                "related": ["Python", "Pydantic", "SQLAlchemy"]},
    "Django": {"category": "framework", "use": "full-stack web applications",
               "related": ["DRF", "Celery", "PostgreSQL"]},
    "DRF": {"category": "framework", "use": "REST APIs in Django projects",
            "related": ["Django", "PostgreSQL"]},
    "Flask": {"category": "framework", "use": "lightweight web services",
              "related": ["Python", "SQLAlchemy"]},
    # Databases
    "PostgreSQL": {"category": "database", "use": "transactional relational data",
                   "related": ["SQLAlchemy", "Alembic"]},
    "MySQL": {"category": "database", "use": "relational data for web apps",
              "related": ["SQLAlchemy"]},
    "MongoDB": {"category": "database", "use": "document storage for flexible schemas",
                "related": ["Python", "PyMongo"]},
    "Elasticsearch": {"category": "search", "use": "full-text search and log analytics",
                      "related": ["Python", "Kibana"]},
    # Cache / Queue
    "Redis": {"category": "cache", "use": "caching, sessions, rate limiting",
              "related": ["Celery", "Python"]},
    "Celery": {"category": "queue", "use": "async background jobs",
               "related": ["Redis", "RabbitMQ", "Django", "FastAPI"]},
    "Kafka": {"category": "streaming", "use": "event streaming and async integration",
              "related": ["Python", "PostgreSQL"]},
    "RabbitMQ": {"category": "queue", "use": "message routing between services",
                 "related": ["Celery", "Python"]},
    # ORM / Migration
    "SQLAlchemy": {"category": "orm", "use": "database access layer",
                   "related": ["Alembic", "PostgreSQL", "FastAPI"]},
    "Alembic": {"category": "migration", "use": "schema version management",
                "related": ["SQLAlchemy", "PostgreSQL"]},
    "Pydantic": {"category": "validation", "use": "data validation and serialization",
                 "related": ["FastAPI", "Python"]},
    # Infrastructure
    "Docker": {"category": "infrastructure", "use": "containerized deployments",
               "related": ["Docker Compose", "Kubernetes"]},
    "Docker Compose": {"category": "infrastructure", "use": "local multi-service orchestration",
                       "related": ["Docker"]},
    "Kubernetes": {"category": "infrastructure", "use": "production container orchestration",
                   "related": ["Docker", "Helm"]},
    "Terraform": {"category": "infrastructure", "use": "infrastructure as code",
                  "related": ["AWS", "GCP"]},
    # Cloud
    "AWS S3": {"category": "storage", "use": "object storage for files and exports",
               "related": ["boto3", "Docker"]},
    "AWS": {"category": "cloud", "use": "cloud infrastructure",
            "related": ["S3", "EC2", "Lambda"]},
    "GCP": {"category": "cloud", "use": "Google cloud services",
            "related": ["BigQuery", "Cloud Run"]},
    # Testing
    "Pytest": {"category": "testing", "use": "unit and integration tests",
               "related": ["Python", "FastAPI"]},
    "unittest": {"category": "testing", "use": "standard library testing",
                 "related": ["Python"]},
    # Observability
    "Grafana": {"category": "monitoring", "use": "dashboards and alerting",
                "related": ["Prometheus", "Loki"]},
    "Prometheus": {"category": "monitoring", "use": "metrics collection",
                   "related": ["Grafana"]},
    # Other
    "Git": {"category": "vcs", "use": "version control"},
    "Nginx": {"category": "proxy", "use": "reverse proxy and load balancer"},
    "gRPC": {"category": "rpc", "use": "internal service communication"},
}

# ─── SENIORITY DEFAULTS ─────────────────────────────────────────────────────────

SENIORITY_DEFAULTS = {
    "Junior": {
        "years": 2,
        "roles": ["Junior Backend Developer", "Backend Developer"],
        "max_complexity": 2,
        "responsibility_scope": "individual feature",
    },
    "Middle": {
        "years": 4,
        "roles": ["Python Backend Developer", "Middle Backend Developer", "Backend Engineer"],
        "max_complexity": 3,
        "responsibility_scope": "module or service",
    },
    "Senior": {
        "years": 7,
        "roles": ["Senior Python Backend Developer", "Senior Backend Engineer", "Lead Backend Developer"],
        "max_complexity": 4,
        "responsibility_scope": "subsystem or platform",
    },
}

# ─── ИМЕНА И ГОРОДА ─────────────────────────────────────────────────────────────

CANDIDATE_NAMES = [
    # Европейские / нейтральные
    "Anton Melnyk", "Daniel Novak", "Ivan Petrov", "Alexei Sorokin", "Dmitri Volkov",
    "Nikita Baranov", "Pavel Kozlov", "Mikhail Lebedev", "Artem Fedorov", "Sergei Morozov",
    "Andrei Popov", "Timur Akhmetov", "Ruslan Nazarov", "Viktor Stepanov", "Oleg Nikitin",
    # Центральноазиатские
    "Samir Karimov", "Timur Saidov", "Farrukh Yusupov", "Bekzod Tashmatov", "Jasur Mirzaev",
    # Европейские
    "Jakub Novák", "Marek Šimánek", "Tomáš Blažek", "Piotr Kowalski", "Łukasz Wiśniewski",
    # Грузинские / Кавказские
    "Giorgi Beridze", "Luka Mchedlishvili", "Nika Gelashvili",
    # Латиноамериканские
    "Carlos Rivera", "Miguel Herrera", "Alejandro Torres",
]

CANDIDATE_CITIES = [
    # Восточная Европа
    "Warsaw", "Prague", "Kraków", "Wrocław", "Bratislava", "Budapest",
    "Kyiv", "Lviv", "Dnipro", "Minsk",
    # Центральная Азия / Кавказ
    "Tbilisi", "Almaty", "Tashkent", "Baku", "Yerevan",
    # Западная Европа
    "Berlin", "Amsterdam", "Vienna", "Lisbon", "Barcelona",
    # Прочие
    "Istanbul", "Belgrade", "Sofia", "Bucharest", "Riga", "Tallinn", "Vilnius",
]

COMPANY_LOCATIONS = [
    "Warsaw, Poland", "Prague, Czech Republic", "Berlin, Germany",
    "Amsterdam, Netherlands", "Vienna, Austria", "Tbilisi, Georgia",
    "Almaty, Kazakhstan", "Kyiv, Ukraine", "Riga, Latvia",
    "Lisbon, Portugal", "Budapest, Hungary", "Bratislava, Slovakia",
    "Istanbul, Turkey", "Barcelona, Spain", "Belgrade, Serbia",
    "Tallinn, Estonia", "Vilnius, Lithuania", "Tashkent, Uzbekistan",
    "London, UK", "Stockholm, Sweden", "Helsinki, Finland",
]


# ─── АУТСОРС / АУТСТАФФ КОМПАНИИ ────────────────────────────────────────────────
# Реальные IT-сервисные компании — могут появляться в любом домене.
# Кандидат работал в этих компаниях и вёл проект для клиента из конкретного домена.

OUTSOURCE_COMPANIES: list[dict] = [
    {
        "name": "EPAM Systems",
        "sector": "IT Services & Outsourcing",
        "employees_range": (40000, 60000),
        "locations": ["Warsaw, Poland", "Kyiv, Ukraine", "Kraków, Poland",
                      "Minsk, Belarus", "Prague, Czech Republic"],
        "description": (
            "A global IT services and product development company delivering "
            "engineering solutions for Fortune 500 clients across multiple industries."
        ),
    },
    {
        "name": "GlobalLogic",
        "sector": "IT Services & Outsourcing",
        "employees_range": (20000, 30000),
        "locations": ["Kyiv, Ukraine", "Kraków, Poland", "Lviv, Ukraine",
                      "Hyderabad, India", "Warsaw, Poland"],
        "description": (
            "A digital product engineering company helping clients design, build, "
            "and deliver digital products and platforms at scale."
        ),
    },
    {
        "name": "SoftServe",
        "sector": "IT Services & Outsourcing",
        "employees_range": (10000, 15000),
        "locations": ["Lviv, Ukraine", "Kyiv, Ukraine", "Warsaw, Poland",
                      "Austin, USA", "Wrocław, Poland"],
        "description": (
            "A technology company and consulting partner delivering software "
            "engineering services across cloud, data, and digital transformation."
        ),
    },
    {
        "name": "Ciklum",
        "sector": "IT Outstaffing",
        "employees_range": (3500, 5000),
        "locations": ["Kyiv, Ukraine", "Warsaw, Poland", "Barcelona, Spain",
                      "London, UK", "Dubai, UAE"],
        "description": (
            "A global digital solutions company providing outstaffing "
            "and custom product engineering services to leading technology companies."
        ),
    },
    {
        "name": "DataArt",
        "sector": "IT Services & Product Engineering",
        "employees_range": (4000, 6000),
        "locations": ["Warsaw, Poland", "Kharkiv, Ukraine", "New York, USA",
                      "London, UK", "Dnipro, Ukraine"],
        "description": (
            "A global software engineering firm that helps financial, healthcare, "
            "media, and hospitality clients build complex custom systems."
        ),
    },
    {
        "name": "Luxoft",
        "sector": "IT Services & Consulting",
        "employees_range": (15000, 20000),
        "locations": ["Warsaw, Poland", "Kyiv, Ukraine", "Dnipro, Ukraine",
                      "Sofia, Bulgaria", "Zurich, Switzerland"],
        "description": (
            "A technology strategy and software engineering firm delivering "
            "digital transformation solutions for banking, automotive, and telecom sectors."
        ),
    },
    {
        "name": "N-iX",
        "sector": "IT Outstaffing & Product Engineering",
        "employees_range": (2000, 2800),
        "locations": ["Lviv, Ukraine", "Warsaw, Poland", "Kraków, Poland", "Kyiv, Ukraine"],
        "description": (
            "A software engineering company providing dedicated development teams "
            "and technology consulting to product companies in Europe and North America."
        ),
    },
    {
        "name": "Intellias",
        "sector": "IT Services & Engineering",
        "employees_range": (3000, 4500),
        "locations": ["Lviv, Ukraine", "Warsaw, Poland", "Kyiv, Ukraine",
                      "Berlin, Germany", "Barcelona, Spain"],
        "description": (
            "A global technology company providing software engineering services "
            "for automotive, financial services, and navigation industries."
        ),
    },
    {
        "name": "Sigma Software",
        "sector": "IT Services",
        "employees_range": (2000, 3000),
        "locations": ["Kharkiv, Ukraine", "Gothenburg, Sweden", "Warsaw, Poland",
                      "Kyiv, Ukraine", "Toronto, Canada"],
        "description": (
            "A software development company delivering engineering and design "
            "services with a focus on automotive, gaming, and enterprise clients."
        ),
    },
    {
        "name": "Mobidev",
        "sector": "Custom Software Development",
        "employees_range": (500, 900),
        "locations": ["Kharkiv, Ukraine", "London, UK", "Kyiv, Ukraine"],
        "description": (
            "A custom software development company specialising in mobile, "
            "web, and AI-driven products for startups and mid-size businesses."
        ),
    },
    {
        "name": "Grid Dynamics",
        "sector": "Digital Transformation & Engineering",
        "employees_range": (3000, 5000),
        "locations": ["Warsaw, Poland", "Kyiv, Ukraine", "Kraków, Poland",
                      "San Jose, USA", "Amsterdam, Netherlands"],
        "description": (
            "A digital transformation and engineering services company, "
            "partnering with retail, finance, and technology enterprises."
        ),
    },
    {
        "name": "Avenga",
        "sector": "IT Services",
        "employees_range": (3000, 4000),
        "locations": ["Warsaw, Poland", "Wrocław, Poland", "Kyiv, Ukraine",
                      "Cologne, Germany", "Philadelphia, USA"],
        "description": (
            "An IT company combining strategy, design, and engineering to "
            "deliver digital products for financial services and healthcare clients."
        ),
    },
]

# Вероятность (0..1) что данная роль будет в аутсорс/аутстафф компании
# (вместо доменной продуктовой компании)
OUTSOURCE_PROBABILITY = 0.30
