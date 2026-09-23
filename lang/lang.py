# =============================================================================
# TRANSLATIONS AND LOCALIZATION
# =============================================================================



SEGMENTS_TITLE = {
    'en': 'Storage Segments',
    'es': 'Segmentos de Almacenamiento',
    'pt': 'Segmentos de Armazenamento',
    'tr': 'Depolama Segmentleri',
}

ADD_SEGMENT_BTN = {
    'en': 'Add Storage Segment',
    'es': 'Añadir Segmento de Almacenamiento',
    'pt': 'Adicionar Segmento de Armazenamento',
    'tr': 'Depolama Segmenti Ekle',
}

REMOVE_SEGMENT_BTN = {
    'en': 'Remove Storage Segment',
    'es': 'Eliminar Segmento de Almacenamiento',
    'pt': 'Remover Segmento de Armazenamento',
    'tr': 'Depolama Segmentini Kaldır',
}

DURATION_DAYS = {
    'en': 'Duration (Days)',
    'es': 'Duración (Días)',
    'pt': 'Duração (Dias)',
    'tr': 'Süre (Gün)',
}

SIM_TAB = {
    'en': 'Simulation',
    'es': 'Simulación',
    'pt': 'Simulação',
    'tr': 'Simülasyon',
}

FALLBACK_MODE = {
    'en': 'Fallback Mode',
    'es': 'Modo de Respaldo',
    'pt': 'Modo de Fallback',
    'tr': 'Yedek Mod',
}

FIXED_TEMP = {
    'en': 'Fixed Temp (°C)',
    'es': 'Temp Fija (°C)',
    'pt': 'Temp Fixa (°C)',
    'tr': 'Sabit Sıcaklık (°C)',
}

FIXED_RH = {
    'en': 'Fixed RH (%)',
    'es': 'HR Fija (%)',
    'pt': 'HR Fixa (%)',
    'tr': 'Sabit Bağıl Nem (%)',
}

START_DATE = {
    'en': 'Start Date',
    'es': 'Fecha de Inicio',
    'pt': 'Data de Início',
    'tr': 'Başlangıç Tarihi',
}

IS_CONTROLLED = {
    'en': 'Is the warehouse controlled?',
    'es': '¿El almacén está controlado?',
    'pt': 'O armazém é controlado?',
    'tr': 'Depo kontrollü mü?',
}

DAILY_READINGS = {
    'en': 'Daily Readings',
    'es': 'Lecturas Diarias',
    'pt': 'Leituras Diárias',
    'tr': 'Günlük Okumalar',
}

DAILY_READINGS_HINT = {
    'en': 'Fill in values you have. Leave empty to let the model estimate.',
    'es': 'Rellene los valores que tenga. Deje vacío para que el modelo estime.',
    'pt': 'Preencha os valores que tem. Deixe vazio para o modelo estimar.',
    'tr': 'Sahip olduğunuz değerleri girin. Modelin tahmin etmesi için boş bırakın.',
}

TEMP_SHORT = {
    'en': 'Temp',
    'es': 'Temp',
    'pt': 'Temp',
    'tr': 'Sıc',
}

RH_SHORT = {
    'en': 'RH',
    'es': 'HR',
    'pt': 'HR',
    'tr': 'BN',
}

ETH_SHORT = {
    'en': 'Eth',
    'es': 'Et',
    'pt': 'Etil',
    'tr': 'Et',
}

RUN_SIMULATION_BTN = {
    'en': 'Run Simulation',
    'es': 'Ejecutar Simulación',
    'pt': 'Executar Simulação',
    'tr': 'Simülasyonu Çalıştır',
}

SIMULATION_COMPLETE = {
    'en': 'Simulation Complete!',
    'es': '¡Simulación Completada!',
    'pt': 'Simulação Concluída!',
    'tr': 'Simülasyon Tamamlandı!',
}

ALGORITHM_USED = {
    'en': 'Algorithm used',
    'es': 'Algoritmo utilizado',
    'pt': 'Algoritmo utilizado',
    'tr': 'Kullanılan algoritma',
}

CONFIGURATION_TITLE = {
    'en': 'Configuration',
    'es': 'Configuración',
    'pt': 'Configuração',
    'tr': 'Konfigürasyon',
}

LANGUAGE_SEL = {
    'en': 'Language',
    'es': 'Idioma',
    'pt': 'Idioma',
    'tr': 'Dil',
}

APP_DESC = {
    'en': (
        "The main mission of the Life Cycle (LC) application is to predict, preserve, and optimize the post-harvest shelf life and commercial quality of fresh fruit throughout transport and storage, helping to avoid food waste.\n\n"
        "To respond to different data realities and distribution chains, the platform provides two models with distinct approaches:\n\n"
        "- **Academic Model**: Developed with fruit biology in mind when ethylene gas measurements are available. Ethylene acts as the natural ripening signal: the fruit can start producing this gas on its own over the days or, if ethylene is already present in the air (for example, coming from neighboring ripe fruit), it picks up that signal and triggers even more of its own production, softening and gaining sugars (Brix) faster. *(Note: Only climacteric fruits have this self-production and continue ripening on their own after harvest; non-climacteric fruits do not have this trigger).* This model uses a quality score with fixed weights.\n\n"
        "- **New Model**: Created for the practical world of distribution where ethylene sensors are usually not available. It introduces another solution for prediction:\n"
        "  1. **Acidity and Maturation Index**: In addition to firmness and Brix, it models acidity loss and calculates the ratio between sugars and acidity, which reflects the real flavor balance of the fruit.\n"
        "  2. **Stakeholder Profiles**: Allows adjusting the quality evaluation to the requirements of whoever manages the product, whether Retailer, Producer, Exporter, or Juice/Jam Industry.\n"
        "  3. **Packaging Protection**: Models the real effect of packaging type, which acts as a barrier against dehydration and slows down fruit respiration.\n"
        "  4. **Air Physics (VPD)**: Calculates the **Vapor Pressure Deficit**, measuring accurately how strongly ambient air pulls moisture out of the fruit.\n"
        "  5. **Commercial Rejection Criteria**: Monitors the active consumption of shelf-life days and invalidates commercialization if mold or quality loss exceeds the limits defined by the stakeholder.\n\n"
        "Both models share the same thermal principle: warmer temperatures exponentially accelerate fruit aging. Both simulate softening and sugar (Brix) gain, and both penalize quality when excessive humidity creates a risk of mold development."
    ),
    'es': (
        "La misión principal de la aplicación Life Cycle (LC) es predecir, preservar y optimizar el tiempo de vida útil poscosecha y la calidad comercial de la fruta fresca a lo largo del transporte y almacenamiento, ayudando a evitar el desperdicio alimentario.\n\n"
        "Para responder a diferentes realidades de datos y cadenas de distribución, la plataforma ofrece dos modelos con enfoques distintos:\n\n"
        "- **Modelo Académico**: Desarrollado pensando en la biología del fruto cuando existen mediciones del gas etileno. El etileno actúa como la señal natural de maduración: el fruto puede empezar a producir este gas por sí solo con el paso de los días o, si ya existe etileno en el aire (por ejemplo, procedente de otras frutas maduras al lado), capta esa señal y dispara aún más su propia producción, ablandándose y ganando azúcares (Brix) más rápido. *(Nota: Solo las frutas climatéricas tienen esta autoproducción y continúan madurando por sí solas tras la cosecha; las no climatéricas no tienen este disparo).* Este modelo utiliza una puntuación de calidad con pesos fijos.\n\n"
        "- **Modelo Nuevo**: Creado para el mundo práctico de la distribución donde normalmente no hay sensores de etileno. Introduce otra solución para la predicción:\n"
        "  1. **Acidez e Índice de Maduración**: Además de la firmeza y del Brix, modela la pérdida de acidez y calcula la relación entre los azúcares y la acidez, que refleja el equilibrio real del sabor de la fruta.\n"
        "  2. **Perfiles de Intervinientes (Stakeholders)**: Permite ajustar la evaluación de calidad a las exigencias de quien gestiona el producto, ya sea Minorista, Productor, Exportador o Industria de zumos/mermeladas.\n"
        "  3. **Protección del Envase**: Modela el efecto real del tipo de envase, que actúa como barrera contra la deshidratación y ralentiza la respiración de la fruta.\n"
        "  4. **Física del Aire (VPD)**: Calcula el **Déficit de Presión de Vapor**, midiendo con exactitud la fuerza con la que el aire exterior extrae humedad del interior del fruto.\n"
        "  5. **Criterio Comercial de Rechazo**: Monitoriza el consumo activo de días de vida útil e invalida la comercialización si el moho o la pérdida de calidad superan los límites definidos por el interviniente.\n\n"
        "Ambos modelos comparten el mismo principio térmico: las temperaturas más cálidas aceleran exponencialmente el envejecimiento de la fruta. Ambos simulan el ablandamiento y la ganancia de azúcares (Brix), y ambos penalizan la calidad cuando la humedad excesiva genera riesgo de aparición de mohos."
    ),
    'pt': (
        "A missão principal da aplicação Life Cycle (LC) é prever, preservar e otimizar o tempo de vida pós-colheita e a qualidade comercial da fruta fresca ao longo do transporte e armazenagem, ajudando a evitar o desperdício alimentar.\n\n"
        "Para responder a diferentes realidades de dados e cadeias de distribuição, a plataforma disponibiliza dois modelos com abordagens distintas:\n\n"
        "- **Modelo Académico**: Desenvolvido a pensar na biologia do fruto quando existem medições do gás etileno. O etileno funciona como o sinal natural de amadurecimento: o fruto pode começar a produzir este gás sozinho com o passar dos dias ou, se já existir etileno no ar (por exemplo, vindo de outras frutas maduras ao lado), apanha esse sinal e dispara ainda mais a sua própria produção, amolecendo e ganhando açúcares (Brix) mais depressa. *(Nota: Apenas as frutas climatéricas têm esta autoprodução e continuam a amadurecer sozinhas após a colheita; as não climatéricas não têm este disparo).* Este modelo usa uma pontuação de qualidade com pesos fixos.\n\n"
        "- **Modelo Novo**: Criado para o mundo prático da distribuição onde normalmente não há sensores de etileno. Introduz outra solução para a previsão:\n"
        "  1. **Acidez e Índice de Maturação**: Além da firmeza e do Brix, modela a perda de acidez e calcula o rácio entre os açúcares e acidez, que reflete o equilíbrio real do sabor da fruta.\n"
        "  2. **Perfis de Intervenientes (Stakeholders)**: Permite ajustar a avaliação de qualidade às exigências de quem gere o produto, seja este Retalhista, Produtor, Exportador ou Indústria de sumos/compotas.\n"
        "  3. **Proteção da Embalagem**: Modela o efeito real do tipo de embalagem, que atua como barreira contra a desidratação e abranda a respiração da fruta.\n"
        "  4. **Física do Ar (VPD)**: Calcula o **Défice de Pressão de Vapor**, medindo com exatidão a força com que o ar exterior retira humidade de dentro do fruto.\n"
        "  5. **Critério Comercial de Rejeição**: Monitoriza o consumo ativo de dias de vida útil e invalida a comercialização caso o bolor ou a perda de qualidade ultrapassem os limites definidos pelo interveniente.\n\n"
        "Ambos os modelos partilham o mesmo princípio térmico: temperaturas mais quentes aceleram exponencialmente o envelhecimento da fruta. Ambos simulam o amolecimento e o ganho de açúcares (Brix), e ambos penalizam a qualidade quando a humidade excessiva gera risco de aparecimento de bolores."
    ),
    'tr': (
        "Life Cycle (LC) uygulamasının temel misyonu, taze meyvelerin taşıma ve depolama boyunca hasat sonrası raf ömrünü ve ticari kalitesini tahmin etmek, korumak ve optimize etmek olup gıda israfını önlemeye yardımcı olmaktır.\n\n"
        "Farklı veri gerçekliklerine ve dağıtım zincirlerine yanıt vermek için platform, iki farklı yaklaşıma sahip model sunar:\n\n"
        "- **Akademik Model**: Etilen gazı ölçümleri mevcut olduğunda meyve biyolojisi düşünülerek geliştirilmiştir. Etilen doğal olgunlaşma sinyali olarak çalışır: meyve günler geçtikçe bu gazı kendi kendine üretmeye başlayabilir veya havada zaten etilen varsa (örneğin yanındaki olgun meyvelerden gelen), bu sinyali alarak kendi üretimini daha da tetikler; böylece daha hızlı yumuşar ve şeker (Brix) kazanır. *(Not: Yalnızca klimakterik meyveler bu kendiliğinden üretime sahiptir ve hasattan sonra kendi başlarına olgunlaşmaya devam eder; klimakterik olmayan meyvelerde bu tetiklenme yoktur).* Bu model sabit ağırlıklı bir kalite puanı kullanır.\n\n"
        "- **Yeni Model**: Etilen sensörlerinin genellikle bulunmadığı pratik dağıtım dünyası için oluşturulmuştur. Tahmin için başka bir çözüm sunar:\n"
        "  1. **Asitlik ve Olgunlaşma İndeksi**: Sertlik ve Brix'in yanı sıra, asitlik kaybını modeller ve meyvenin gerçek tat dengesini yansıtan şeker ve asitlik oranını hesaplar.\n"
        "  2. **Paydaş Profilleri (Stakeholders)**: Kalite değerlendirmesini ürünü yöneten tarafın (Perakendeci, Üretici, İhracatçı veya Meyve suyu/reçel sanayisi) gereksinimlerine göre ayarlamayı sağlar.\n"
        "  3. **Ambalaj Koruması**: Dehidrasyona karşı bir bariyer görevi gören ve meyve solunumunu yavaşlatan ambalaj türünün gerçek etkisini modeller.\n"
        "  4. **Hava Fiziği (VPD)**: Dış havanın meyvenin içinden ne kadar güçlü nem çektiğini hassasiyetle ölçen **Buhar Basıncı Açığı**nı hesaplar.\n"
        "  5. **Ticari Red Kriteri**: Raf ömrü günlerinin aktif tüketimini izler ve küf veya kalite kaybı paydaş tarafından belirlenen sınırları aştığında ticarileştirmeyi geçersiz kılar.\n\n"
        "Her iki model de aynı termal ilkeyi paylaşır: daha sıcak sıcaklıklar meyvenin yaşlanmasını katlanarak hızlandırır. Her ikisi de yumuşamayı ve şeker (Brix) kazanımını simüle eder ve aşırı nem küf oluşumu riski yarattığında her ikisi de kaliteyi cezalandırır."
    ),
}


VIEW_FRUIT_PARAMS_TITLE = {
    'en': 'View Fruit Parameters',
    'es': 'Ver Parámetros de Fruta',
    'pt': 'Ver Parâmetros da Fruta',
    'tr': 'Meyve Parametrelerini Görüntüle',
}

SELECT_MODEL_LBL = {
    'en': 'Select Model',
    'es': 'Seleccionar Modelo',
    'pt': 'Selecionar Modelo',
    'tr': 'Model Seçin',
}

FRUIT_LBL = {
    'en': 'Fruit',
    'es': 'Fruta',
    'pt': 'Fruta',
    'tr': 'Meyve',
}

REGION_LBL = {
    'en': 'Region',
    'es': 'Región',
    'pt': 'Região',
    'tr': 'Bölge',
}

PACKAGING_LBL = {
    'en': 'Packaging',
    'es': 'Embalaje',
    'pt': 'Embalagem',
    'tr': 'Paketleme',
}

FIRMNESS_LBL = {
    'en': 'Firmness (N)',
    'es': 'Firmeza (N)',
    'pt': 'Firmeza (N)',
    'tr': 'Sertlik (N)',
}

BRIX_LBL = {
    'en': 'Brix',
    'es': 'Brix',
    'pt': 'Brix',
    'tr': 'Brix',
}

ACIDITY_LBL = {
    'en': 'Acidity',
    'es': 'Acidez',
    'pt': 'Acidez',
    'tr': 'Asidite',
}

SIMULATING_SPINNER = {
    'en': 'Simulating...',
    'es': 'Simulando...',
    'pt': 'A simular...',
    'tr': 'Simüle ediliyor...',
}

CREATE_NEW_PRESET_TITLE = {
    'en': 'Create New Fruit Parameter',
    'es': 'Crear Nuevo Ajuste',
    'pt': 'Criar Nova Predefinição',
    'tr': 'Yeni Ön Ayar Oluştur',
}

FRUIT_KEY_LBL = {
    'en': 'Fruit Key (e.g., apple_gala_custom)',
    'es': 'Clave de Fruta (ej., manzana_gala_custom)',
    'pt': 'Chave da Fruta (ex., maca_gala_custom)',
    'tr': 'Meyve Anahtarı (örn., elma_gala_ozel)',
}

GENERAL_KINETICS_TITLE = {
    'en': 'General / Kinetics',
    'es': 'General / Cinética',
    'pt': 'Geral / Cinética',
    'tr': 'Genel / Kinetik',
}

ETHYLENE_PROP_TITLE = {
    'en': 'Ethylene Properties',
    'es': 'Propiedades de Etileno',
    'pt': 'Propriedades do Etileno',
    'tr': 'Etilen Özellikleri',
}

MOLD_PROP_TITLE = {
    'en': 'Mold Properties',
    'es': 'Propiedades de Moho',
    'pt': 'Propriedades de Bolor',
    'tr': 'Küf Özellikleri',
}

SAVE_PRESET_BTN = {
    'en': 'Save Custom Fruit Parameter',
    'es': 'Guardar Ajuste',
    'pt': 'Salvar Predefinição Personalizada',
    'tr': 'Özel Ön Ayarı Kaydet',
}

PLEASE_ENTER_KEY_ERR = {
    'en': 'Please enter a Fruit Key.',
    'es': 'Por favor, introduce una Clave de Fruta.',
    'pt': 'Por favor, insira uma Chave de Fruta.',
    'tr': 'Lütfen bir Meyve Anahtarı girin.',
}

PRESET_CREATED_SUCC = {
    'en': 'Fruit Parameter created successfully!',
    'es': '¡Ajuste creado con éxito!',
    'pt': 'Predefinição criada com sucesso!',
    'tr': 'Ön ayar başarıyla oluşturuldu!',
}

PRESET_SAVE_ERR = {
    'en': 'Error saving fruit parameter:',
    'es': 'Error al guardar el ajuste:',
    'pt': 'Erro ao salvar a predefinição:',
    'tr': 'Ön ayar kaydetme hatası:',
}

PACKAGING_TRANS = {
    'en': {
        "Granel (Sem embalagem)": "Bulk (No packaging)",
        "Caixa de Cartão Aberta": "Open Cardboard Box",
        "Saco Plástico Perfurado": "Perforated Plastic Bag",
        "MAP (Atmosfera Modificada) / Plástico Selado": "MAP / Sealed Plastic"
    },
    'es': {
        "Granel (Sem embalagem)": "A Granel (Sin envase)",
        "Caixa de Cartão Aberta": "Caja de Cartón Abierta",
        "Saco Plástico Perfurado": "Bolsa de Plástico Perforada",
        "MAP (Atmosfera Modificada) / Plástico Selado": "EAM / Plástico Sellado"
    },
    'pt': {
        "Granel (Sem embalagem)": "Granel (Sem embalagem)",
        "Caixa de Cartão Aberta": "Caixa de Cartão Aberta",
        "Saco Plástico Perfurado": "Saco Plástico Perfurado",
        "MAP (Atmosfera Modificada) / Plástico Selado": "MAP (Atmosfera Modificada) / Plástico Selado"
    },
    'tr': {
        "Granel (Sem embalagem)": "Dökme (Ambalajsız)",
        "Caixa de Cartão Aberta": "Açık Karton Kutu",
        "Saco Plástico Perfurado": "Delikli Plastik Torba",
        "MAP (Atmosfera Modificada) / Plástico Selado": "MAP / Sızdırmaz Plastik"
    }
}

ENABLE_ETHYLENE_TOGGLE = {
    'en': 'Enable Ethylene Properties (Academic Model)',
    'es': 'Habilitar Propiedades de Etileno (Modelo Académico)',
    'pt': 'Ativar Propriedades de Etileno (Modelo Académico)',
    'tr': 'Etilen Özelliklerini Etkinleştir (Akademik Model)',
}

KPI_TITLE = {
    'en': 'Key Performance Indicators',
    'es': 'Indicadores Clave de Rendimiento',
    'pt': 'Indicadores de Desempenho',
    'tr': 'Temel Performans Göstergeleri',
}

KPI_DAYS_SIM = {
    'en': 'Days Simulated',
    'es': 'Días Simulados',
    'pt': 'Dias Simulados',
    'tr': 'Simüle Edilen Gün',
}

KPI_FINAL_QUALITY = {
    'en': 'Final Quality',
    'es': 'Calidad Final',
    'pt': 'Qualidade Final',
    'tr': 'Son Kalite',
}

KPI_FINAL_FIRMNESS = {
    'en': 'Final Firmness',
    'es': 'Firmeza Final',
    'pt': 'Firmeza Final',
    'tr': 'Son Sertlik',
}

KPI_FINAL_BRIX = {
    'en': 'Final Brix',
    'es': 'Brix Final',
    'pt': 'Brix Final',
    'tr': 'Son Brix',
}

KPI_FINAL_ACIDITY = {
    'en': 'Final Acidity',
    'es': 'Acidez Final',
    'pt': 'Acidez Final',
    'tr': 'Son Asidite',
}

CONT_SIM_RESULTS_TITLE = {
    'en': 'Continuous Simulation Results',
    'es': 'Resultados de Simulación Continua',
    'pt': 'Resultados da Simulação Contínua',
    'tr': 'Sürekli Simülasyon Sonuçları',
}

VIEW_COMPLEX_PARAMS_TITLE = {
    'en': 'View Complex Parameters:',
    'es': 'Ver Parámetros Complejos:',
    'pt': 'Ver Parâmetros Complexos:',
    'tr': 'Karmaşık Parametreleri Görüntüle:',
}

NO_PARAMS_FOUND_WARN = {
    'en': 'No parameters found for {fruit} in {model} model.',
    'es': 'No se encontraron parámetros para {fruit} en el modelo {model}.',
    'pt': 'Não foram encontrados parâmetros para {fruit} no modelo {model}.',
    'tr': '{model} modelinde {fruit} için parametre bulunamadı.',
}

STAKEHOLDER_OVERRIDES_TITLE = {
    'en': 'Stakeholder Overrides',
    'es': 'Anulaciones de Interesados',
    'pt': 'Substituições de Stakeholders',
    'tr': 'Paydaş Geçersiz Kılmaları',
}

STAKEHOLDER_OVERRIDES_CAPTION = {
    'en': 'Leave fields empty to use default values. Only filled rows will be saved.',
    'es': 'Deje los campos vacíos para usar los valores predeterminados. Solo se guardarán las filas llenas.',
    'pt': 'Deixe os campos vazios para usar os valores padrão. Apenas as linhas preenchidas serão salvas.',
    'tr': 'Varsayılan değerleri kullanmak için alanları boş bırakın. Sadece doldurulmuş satırlar kaydedilecektir.',
}

CHART_DAYS = {
    'en': 'Days',
    'es': 'Días',
    'pt': 'Dias',
    'tr': 'Gün',
}

CHART_QUALITY_INDEX = {
    'en': 'Quality Index',
    'es': 'Índice de Calidad',
    'pt': 'Índice de Qualidade',
    'tr': 'Kalite Endeksi',
}

CHART_QUALITY = {
    'en': 'Quality',
    'es': 'Calidad',
    'pt': 'Qualidade',
    'tr': 'Kalite',
}

STAKEHOLDER_ROLE_LBL = {
    'en': 'Stakeholder Role',
    'es': 'Rol de Interesado',
    'pt': 'Perfil de Stakeholder',
    'tr': 'Paydaş Rolü',
}

CHART_BASE_QUALITY = {
    'en': 'Base Quality',
    'es': 'Calidad Base',
    'pt': 'Qualidade Base',
    'tr': 'Temel Kalite',
}


UPLOAD_DATA_TAB = {
    'en': "Upload Data (Excel/JSON)",
    'es': "Subir Datos (Excel/JSON)",
    'pt': "Upload de Dados (Excel/JSON)",
    'tr': "Veri Yükle (Excel/JSON)",
}

EXCEL_TIPS_TITLE = {
    'en': "💡 Tips for Excel Formatting",
    'es': "💡 Consejos para Formato Excel",
    'pt': "💡 Dicas para Formatação no Excel",
    'tr': "💡 Excel Formatı İçin İpuçları",
}

EXCEL_TIPS_TEXT = {
    'en': "- Add daily inputs for environment conditions (e.g., `Temperature_C`, `Humidity_Percent`).\n- **Real data is completely optional.** If you have real measurements to compare, add them directly on the same row using columns like `Real_Firmness`, `Real_BRIX`, `Real_Acidity`, or `Real_Quality`.\n- **Regions:** `PT-NL`, `PT-NI`, `PT-CL`, `PT-CI`, `PT-LVT`, `PT-AL`, `PT-ALG`, `PT-SM`, `PT-MAD`, `PT-ACO`\n- **Packaging:** `Granel (Sem embalagem)`, `Caixa de Cartao Aberta`, `Saco Plástico Perfurado`, `MAP (Atmosfera Modificada) / Plástico Selado`\n- 💡 **Note:** If `Ethylene_ppm` values are provided for all rows, the simulation will automatically use the **Academic Model**.",
    'es': "- Añada entradas diarias para las condiciones ambientales (ej., `Temperature_C`, `Humidity_Percent`).\n- **Los datos reales son completamente opcionales.** Si tiene medidas reales para comparar, añádalas directamente en la misma fila utilizando columnas como `Real_Firmness`, `Real_BRIX`, `Real_Acidity` o `Real_Quality`.\n- **Regiones:** `PT-NL`, `PT-NI`, `PT-CL`, `PT-CI`, `PT-LVT`, `PT-AL`, `PT-ALG`, `PT-SM`, `PT-MAD`, `PT-ACO`\n- **Embalaje:** `Granel (Sem embalagem)`, `Caixa de Cartao Aberta`, `Saco Plástico Perfurado`, `MAP (Atmosfera Modificada) / Plástico Selado`\n- 💡 **Nota:** Si se proporcionan valores de `Ethylene_ppm` para todas las filas, la simulación utilizará automáticamente el **Modelo Académico**.",
    'pt': "- Adicione dados diários para condições ambientais (ex., `Temperature_C`, `Humidity_Percent`).\n- **Dados reais são completamente opcionais.** Se tem medições reais para comparar, adicione-as diretamente na mesma linha usando colunas como `Real_Firmness`, `Real_BRIX`, `Real_Acidity` ou `Real_Quality`.\n- **Regiões:** `PT-NL`, `PT-NI`, `PT-CL`, `PT-CI`, `PT-LVT`, `PT-AL`, `PT-ALG`, `PT-SM`, `PT-MAD`, `PT-ACO`\n- **Embalagem:** `Granel (Sem embalagem)`, `Caixa de Cartao Aberta`, `Saco Plástico Perfurado`, `MAP (Atmosfera Modificada) / Plástico Selado`\n- 💡 **Nota:** Se os valores de `Ethylene_ppm` forem fornecidos para todas as linhas, a simulação usará automaticamente o **Modelo Académico**.",
    'tr': "- Çevre koşulları için günlük girdiler ekleyin (örn., `Temperature_C`, `Humidity_Percent`).\n- **Gerçek veriler tamamen isteğe bağlıdır.** Karşılaştırılacak gerçek ölçümleriniz varsa, bunları `Real_Firmness`, `Real_BRIX`, `Real_Acidity` veya `Real_Quality` gibi sütunlar kullanarak aynı satıra ekleyin.\n- **Bölgeler:** `PT-NL`, `PT-NI`, `PT-CL`, `PT-CI`, `PT-LVT`, `PT-AL`, `PT-ALG`, `PT-SM`, `PT-MAD`, `PT-ACO`\n- **Paketleme:** `Granel (Sem embalagem)`, `Caixa de Cartao Aberta`, `Saco Plástico Perfurado`, `MAP (Atmosfera Modificada) / Plástico Selado`\n- 💡 **Not:** Tüm satırlar için `Ethylene_ppm` değerleri sağlanırsa, simülasyon otomatik olarak **Akademik Model**'i kullanacaktır."
}

SIM_FROM_EXCEL_TITLE = {
    'en': "Simulation from Excel",
    'es': "Simulación desde Excel",
    'pt': "Simulação de Excel",
    'tr': "Excel'den Simülasyon",
}

SIM_FROM_JSON_TITLE = {
    'en': "Simulation from JSON",
    'es': "Simulación desde JSON",
    'pt': "Simulação de JSON",
    'tr': "JSON'dan Simülasyon",
}

ALGORITHM_NAMES = {
    'en': {
        'ode_new': 'New Model',
        'ode_academic': 'Academical Model'
    },
    'es': {
        'ode_new': 'Nuevo Modelo',
        'ode_academic': 'Modelo Académico'
    },
    'pt': {
        'ode_new': 'Novo Modelo',
        'ode_academic': 'Modelo Académico'
    },
    'tr': {
        'ode_new': 'Yeni Model',
        'ode_academic': 'Akademik Model'
    }
}

FRUIT_NAMES = {
    'en': {
        'kiwi_hayward': 'Kiwi (Hayward)',
        'kiwi_baby': 'Kiwi (Baby/Berry)',
        'apple_golden': 'Apple (Golden)',
        'apple_reineta': 'Apple (Reineta)',
        'apple_gala': 'Apple (Gala)',
        'apple_fuji': 'Apple (Fuji)',
        'orange': 'Orange',
        'banana': 'Banana',
        'blueberry': 'Blueberry',
        'raspberry': 'Raspberry',
        'pear': 'Pear',
        'plum': 'Plum',
        'peach': 'Peach',
        'cherry': 'Cherry',
        'strawberry': 'Strawberry',
        'grape': 'Grape',
        'fig': 'Fig',
        'melon': 'Melon'
    },
    'es': {
        'kiwi_hayward': 'Kiwi (Hayward)',
        'kiwi_baby': 'Kiwi (Baby/Berry)',
        'apple_golden': 'Manzana (Golden)',
        'apple_reineta': 'Manzana (Reineta)',
        'apple_gala': 'Manzana (Gala)',
        'apple_fuji': 'Manzana (Fuji)',
        'orange': 'Naranja',
        'banana': 'Plátano',
        'blueberry': 'Arándano',
        'raspberry': 'Frambuesa',
        'pear': 'Pera',
        'plum': 'Ciruela',
        'peach': 'Melocotón',
        'cherry': 'Cereza',
        'strawberry': 'Fresa',
        'grape': 'Uva',
        'fig': 'Higo',
        'melon': 'Melón'
    },
    'pt': {
        'kiwi_hayward': 'Kiwi (Hayward)',
        'kiwi_baby': 'Kiwi (Baby/Berry)',
        'apple_golden': 'Maçã (Golden)',
        'apple_reineta': 'Maçã (Reineta)',
        'apple_gala': 'Maçã (Gala)',
        'apple_fuji': 'Maçã (Fuji)',
        'orange': 'Laranja',
        'banana': 'Banana',
        'blueberry': 'Mirtilo',
        'raspberry': 'Framboesa',
        'pear': 'Pera',
        'plum': 'Ameixa',
        'peach': 'Pêssego',
        'cherry': 'Cereja',
        'strawberry': 'Morango',
        'grape': 'Uva',
        'fig': 'Figo',
        'melon': 'Melão'
    },
    'tr': {
        'kiwi_hayward': 'Kivi (Hayward)',
        'kiwi_baby': 'Kivi (Bebek/Meyve)',
        'apple_golden': 'Elma (Golden)',
        'apple_reineta': 'Elma (Reineta)',
        'apple_gala': 'Elma (Gala)',
        'apple_fuji': 'Elma (Fuji)',
        'orange': 'Portakal',
        'banana': 'Muz',
        'blueberry': 'Yaban Mersini',
        'raspberry': 'Ahududu',
        'pear': 'Armut',
        'plum': 'Erik',
        'peach': 'Şeftali',
        'cherry': 'Kiraz',
        'strawberry': 'Çilek',
        'grape': 'Üzüm',
        'fig': 'İncir',
        'melon': 'Kavun'
    }
}


NO_ETHYLENE_LBL = {
    'en': ' (No Ethylene)',
    'pt': ' (Sem Etileno)',
    'es': ' (Sin Etileno)',
    'tr': ' (Etilensiz)'
}

WITH_ETHYLENE_LBL = {
    'en': ' (With Ethylene)',
    'pt': ' (Com Etileno)',
    'es': ' (Con Etileno)',
    'tr': ' (Etilenli)'
}

FRUITS_TAB = {
    'en': 'Fruits',
    'pt': 'Frutas',
    'es': 'Frutas',
    'tr': 'Meyveler'
}

DOWNLOAD_EXCEL_EXAMPLE = {
    'en': 'Download Excel Example',
    'pt': 'Baixar Exemplo Excel',
    'es': 'Descargar Ejemplo Excel',
    'tr': 'Excel Örneğini İndir'
}

DOWNLOAD_JSON_EXAMPLE = {
    'en': 'Download JSON Example',
    'pt': 'Baixar Exemplo JSON',
    'es': 'Descargar Ejemplo JSON',
    'tr': 'JSON Örneğini İndir'
}

UPLOAD_DATA_EXCEL_JSON = {
    'en': 'Upload Data (Excel or JSON)',
    'pt': 'Upload Dados (Excel ou JSON)',
    'es': 'Subir Datos (Excel o JSON)',
    'tr': 'Veri Yükle (Excel veya JSON)'
}
