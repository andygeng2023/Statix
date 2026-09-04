from __future__ import annotations
import os
from pathlib import Path
import streamlit as st

APP_NAME = "Statix"
ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = ROOT / "artifacts"
MODEL_PATH = ARTIFACT_DIR / "statix_model.joblib"
MODEL_META_PATH = ARTIFACT_DIR / "model_meta.json"
SEQUENCE_LENGTH = 64
HORIZON = 5
MAX_SCAN = 2000
QUOTE_TTL = 15
HISTORY_TTL = 300
SEARCH_TTL = 600
SCANNER_STALE_MINUTES = 30

LANGUAGES = {
    "English":"en", "Français":"fr", "Español":"es", "Italiano":"it",
    "Deutsch":"de", "中文":"zh", "日本語":"ja", "한국어":"ko", "Português":"pt",
}

TEXT = {
"en": {"home":"Home","stocks":"Stocks","discover":"Discover","settings":"Settings","market_pulse":"Live market pulse","top_stocks":"Top stocks","discover_short":"Discover","watch_suggestions":"From your watchlist","search":"Search stocks","watchlist":"Watchlist","provider":"Provider","language":"Language","refresh":"Refresh","analyze":"Analyze","watch":"Watch","remove":"Remove","no_results":"No securities found.","scanner":"Scanner & recommendations","queue":"Run scanner","latest":"Latest scan","confidence":"Confidence","reliability":"Reliability","expected":"Expected 5D return","price":"Price","change":"Day change","save":"Save settings","identity":"Identity","data_source":"Data source","auto":"Automatic fallback","model":"Prediction model","no_model":"Train and install the model before predictions are available."},
"fr": {"home":"Accueil","stocks":"Actions","discover":"Découvrir","settings":"Paramètres","market_pulse":"Marché en direct","top_stocks":"Actions populaires","discover_short":"Découvrir","watch_suggestions":"Depuis votre liste","search":"Rechercher des actions","watchlist":"Liste de suivi","provider":"Fournisseur","language":"Langue","refresh":"Actualiser","analyze":"Analyser","watch":"Suivre","remove":"Retirer","no_results":"Aucun titre trouvé.","scanner":"Scanner et recommandations","queue":"Lancer le scanner","latest":"Dernier scan","confidence":"Confiance","reliability":"Fiabilité","expected":"Rendement prévu à 5 jours","price":"Prix","change":"Variation du jour","save":"Enregistrer","identity":"Identité","data_source":"Source des données","auto":"Repli automatique","model":"Modèle de prévision","no_model":"Entraînez et installez le modèle avant les prévisions."},
"es": {"home":"Inicio","stocks":"Acciones","discover":"Descubrir","settings":"Ajustes","market_pulse":"Mercado en vivo","top_stocks":"Acciones destacadas","discover_short":"Descubrir","watch_suggestions":"De tu lista","search":"Buscar acciones","watchlist":"Lista de seguimiento","provider":"Proveedor","language":"Idioma","refresh":"Actualizar","analyze":"Analizar","watch":"Seguir","remove":"Quitar","no_results":"No se encontraron valores.","scanner":"Escáner y recomendaciones","queue":"Ejecutar escáner","latest":"Último escaneo","confidence":"Confianza","reliability":"Fiabilidad","expected":"Rentabilidad prevista a 5 días","price":"Precio","change":"Cambio diario","save":"Guardar","identity":"Identidad","data_source":"Fuente de datos","auto":"Fallback automático","model":"Modelo de predicción","no_model":"Entrena e instala el modelo antes de usar predicciones."},
"it": {"home":"Home","stocks":"Azioni","discover":"Scopri","settings":"Impostazioni","market_pulse":"Mercato in tempo reale","top_stocks":"Azioni principali","discover_short":"Scopri","watch_suggestions":"Dalla tua lista","search":"Cerca azioni","watchlist":"Lista osservati","provider":"Provider","language":"Lingua","refresh":"Aggiorna","analyze":"Analizza","watch":"Segui","remove":"Rimuovi","no_results":"Nessun titolo trovato.","scanner":"Scanner e raccomandazioni","queue":"Avvia scanner","latest":"Ultima scansione","confidence":"Confidenza","reliability":"Affidabilità","expected":"Rendimento previsto a 5 giorni","price":"Prezzo","change":"Variazione giornaliera","save":"Salva","identity":"Identità","data_source":"Fonte dati","auto":"Fallback automatico","model":"Modello predittivo","no_model":"Addestra e installa il modello prima delle previsioni."},
"de": {"home":"Start","stocks":"Aktien","discover":"Entdecken","settings":"Einstellungen","market_pulse":"Live-Markt","top_stocks":"Top-Aktien","discover_short":"Entdecken","watch_suggestions":"Aus deiner Liste","search":"Aktien suchen","watchlist":"Beobachtungsliste","provider":"Datenanbieter","language":"Sprache","refresh":"Aktualisieren","analyze":"Analysieren","watch":"Beobachten","remove":"Entfernen","no_results":"Keine Wertpapiere gefunden.","scanner":"Scanner und Empfehlungen","queue":"Scanner starten","latest":"Letzter Scan","confidence":"Konfidenz","reliability":"Zuverlässigkeit","expected":"Erwartete 5-Tage-Rendite","price":"Preis","change":"Tagesänderung","save":"Speichern","identity":"Identität","data_source":"Datenquelle","auto":"Automatischer Fallback","model":"Prognosemodell","no_model":"Modell trainieren und installieren, bevor Prognosen verfügbar sind."},
"zh": {"home":"首页","stocks":"股票","discover":"发现","settings":"设置","market_pulse":"实时市场脉搏","top_stocks":"热门股票","discover_short":"发现","watch_suggestions":"自选股建议","search":"搜索股票","watchlist":"自选列表","provider":"数据源","language":"语言","refresh":"刷新","analyze":"分析","watch":"加入自选","remove":"移除","no_results":"未找到证券。","scanner":"扫描与推荐","queue":"运行扫描","latest":"最近扫描","confidence":"置信度","reliability":"可靠性","expected":"5日预期收益","price":"价格","change":"日涨跌","save":"保存设置","identity":"身份","data_source":"数据来源","auto":"自动回退","model":"预测模型","no_model":"请先训练并安装模型。"},
"ja": {"home":"ホーム","stocks":"銘柄","discover":"発見","settings":"設定","market_pulse":"ライブ市場","top_stocks":"注目銘柄","discover_short":"発見","watch_suggestions":"ウォッチリストから","search":"銘柄を検索","watchlist":"ウォッチリスト","provider":"プロバイダー","language":"言語","refresh":"更新","analyze":"分析","watch":"追加","remove":"削除","no_results":"証券が見つかりません。","scanner":"スキャナーとおすすめ","queue":"スキャン実行","latest":"最新スキャン","confidence":"信頼度","reliability":"信頼性","expected":"5日予想リターン","price":"価格","change":"日次変化","save":"設定を保存","identity":"ID","data_source":"データソース","auto":"自動フォールバック","model":"予測モデル","no_model":"予測前にモデルを学習・配置してください。"},
"ko": {"home":"홈","stocks":"종목","discover":"발견","settings":"설정","market_pulse":"실시간 시장","top_stocks":"주요 종목","discover_short":"발견","watch_suggestions":"관심종목 기반","search":"종목 검색","watchlist":"관심종목","provider":"데이터 제공자","language":"언어","refresh":"새로고침","analyze":"분석","watch":"추가","remove":"삭제","no_results":"증권을 찾을 수 없습니다.","scanner":"스캐너 및 추천","queue":"스캔 실행","latest":"최근 스캔","confidence":"신뢰도","reliability":"신뢰성","expected":"5일 예상 수익률","price":"가격","change":"일간 변동","save":"설정 저장","identity":"신원","data_source":"데이터 소스","auto":"자동 대체","model":"예측 모델","no_model":"예측 전에 모델을 학습하고 설치하세요."},
"pt": {"home":"Início","stocks":"Ações","discover":"Descobrir","settings":"Configurações","market_pulse":"Mercado ao vivo","top_stocks":"Ações em destaque","discover_short":"Descobrir","watch_suggestions":"Da sua lista","search":"Pesquisar ações","watchlist":"Lista de acompanhamento","provider":"Provedor","language":"Idioma","refresh":"Atualizar","analyze":"Analisar","watch":"Adicionar","remove":"Remover","no_results":"Nenhum título encontrado.","scanner":"Scanner e recomendações","queue":"Executar scanner","latest":"Última varredura","confidence":"Confiança","reliability":"Confiabilidade","expected":"Retorno esperado em 5 dias","price":"Preço","change":"Variação diária","save":"Salvar","identity":"Identidade","data_source":"Fonte de dados","auto":"Fallback automático","model":"Modelo de previsão","no_model":"Treine e instale o modelo antes das previsões."},
}

def secret(name, default=None):
    try: return st.secrets.get(name, default)
    except Exception: return os.getenv(name, default)

def database_url():
    direct = secret("database_url") or os.getenv("DATABASE_URL")
    if direct: return str(direct).strip()
    try:
        pg=st.secrets.get("connections",{}).get("postgresql",{})
        if pg:
            from urllib.parse import quote_plus
            return f"postgresql+psycopg://{quote_plus(str(pg['username']))}:{quote_plus(str(pg['password']))}@{pg['host']}:{pg.get('port',5432)}/{pg['database']}"
    except Exception: pass
    return None

def require_auth():
    v=secret("require_auth",False)
    return str(v).lower() in {"1","true","yes","on"} if isinstance(v,str) else bool(v)
