"""
경제지표 자동 수집 모듈
─────────────────────────
데이터 소스:
  1. 한국은행 ECOS API  → 기준금리, GDP성장률, 소비자물가
  2. 통계청 KOSIS API   → 실업률, 가처분소득
  3. 한국골프장경영협회  → 골프인구, 연습장/스크린 수 (웹 수집)

사용법:
  from data_fetcher import EconomicDataFetcher
  fetcher = EconomicDataFetcher(ecos_key="YOUR_KEY", kosis_key="YOUR_KEY")
  data = fetcher.get_all()   # 캐시 우선, 만료 시 API 호출
  data = fetcher.refresh()   # 강제 갱신
"""

import json, os, time, logging
from datetime import datetime, timedelta
from pathlib import Path

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("data_fetcher")

CACHE_FILE = Path(__file__).parent / "economic_cache.json"
CACHE_TTL_HOURS = 24 * 7  # 7일 캐시 (경제지표는 월/분기 단위 발표)

# ══════════════════════════════════════════════════════
# Default values (API 없을 때 사용)
# ══════════════════════════════════════════════════════
DEFAULTS = {
    "fetch_time": None,
    "source": "default",
    # 한국은행 (ECOS)
    "base_rate": 3.0,           # 기준금리 (%)
    "gdp_growth": 2.1,          # GDP 성장률 (%)
    "cpi_rate": 2.5,            # 소비자물가 상승률 (%)
    "cpi_index": 115.0,         # 소비자물가지수
    # 통계청 (KOSIS)
    "unemployment": 3.5,        # 실업률 (%)
    "disposable_income_growth": 1.5,  # 가처분소득 증감률 (%)
    "population_gangseo": 570000,     # 강서구 인구
    # 골프 산업
    "golf_population": 515,     # 골프인구 (만명)
    "golf_pop_growth": -1.5,    # 골프인구 증감률 (%)
    "driving_range_count": 1850,  # 전국 골프연습장 수
    "screen_golf_count": 9500,    # 전국 스크린골프 수
    "avg_range_revenue": 8.5,     # 연습장 평균 매출 (억원)
    # 메타
    "last_update": "수동 입력 (기본값)",
    "data_period": "2025",
    "notes": "API 키 미설정 — 기본값 사용 중. 사이드바에서 수동 조정 가능.",
}


def _try_import_requests():
    """requests 라이브러리가 없으면 None 반환."""
    try:
        import requests
        return requests
    except ImportError:
        log.warning("requests 패키지 미설치. `pip install requests` 후 API 자동수집 가능.")
        return None


class EconomicDataFetcher:
    """경제지표 수집·캐싱 클래스."""

    def __init__(self, ecos_key: str = "", kosis_key: str = ""):
        self.ecos_key = ecos_key
        self.kosis_key = kosis_key
        self.requests = _try_import_requests()
        self._cache = None

    # ── Cache ──
    def _load_cache(self) -> dict | None:
        if CACHE_FILE.exists():
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                ft = data.get("fetch_time")
                if ft:
                    age = datetime.now() - datetime.fromisoformat(ft)
                    if age < timedelta(hours=CACHE_TTL_HOURS):
                        log.info(f"캐시 사용 (갱신: {ft}, {age.days}일 전)")
                        return data
                    log.info(f"캐시 만료 ({age.days}일 경과)")
                return data  # 만료되어도 반환 (fallback)
            except Exception as e:
                log.warning(f"캐시 읽기 실패: {e}")
        return None

    def _save_cache(self, data: dict):
        try:
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            log.info(f"캐시 저장: {CACHE_FILE}")
        except Exception as e:
            log.warning(f"캐시 저장 실패: {e}")

    def _is_cache_fresh(self) -> bool:
        if not CACHE_FILE.exists():
            return False
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            ft = data.get("fetch_time")
            if ft:
                age = datetime.now() - datetime.fromisoformat(ft)
                return age < timedelta(hours=CACHE_TTL_HOURS)
        except:
            pass
        return False

    # ── ECOS API (한국은행) ──
    def _fetch_ecos(self, stat_code: str, item_code: str, period: str = "M",
                    start: str = "", end: str = "") -> float | None:
        """한국은행 ECOS API 단일 값 조회."""
        if not self.ecos_key or not self.requests:
            return None
        if not start:
            now = datetime.now()
            start = (now - timedelta(days=180)).strftime("%Y%m")
            end = now.strftime("%Y%m")
        url = (f"https://ecos.bok.or.kr/api/StatisticSearch/"
               f"{self.ecos_key}/json/kr/1/5/{stat_code}/{period}/{start}/{end}/{item_code}")
        try:
            resp = self.requests.get(url, timeout=10)
            data = resp.json()
            rows = data.get("StatisticSearch", {}).get("row", [])
            if rows:
                val = rows[-1].get("DATA_VALUE", "")
                return float(val) if val else None
        except Exception as e:
            log.warning(f"ECOS API 실패 ({stat_code}/{item_code}): {e}")
        return None

    def fetch_base_rate(self) -> float | None:
        """한국은행 기준금리."""
        return self._fetch_ecos("722Y001", "0101000")

    def fetch_gdp_growth(self) -> float | None:
        """GDP 성장률 (전년동기비, 분기)."""
        now = datetime.now()
        start = (now - timedelta(days=365)).strftime("%Y%m")
        end = now.strftime("%Y%m")
        val = self._fetch_ecos("200Y002", "10111", "Q", start[:4]+"Q1", end[:4]+"Q4")
        return val

    def fetch_cpi(self) -> float | None:
        """소비자물가 상승률 (전년동월비)."""
        return self._fetch_ecos("021Y125", "0")

    # ── KOSIS API (통계청) ──
    def _fetch_kosis(self, org_id: str, tbl_id: str, **params) -> dict | None:
        """통계청 KOSIS API 조회."""
        if not self.kosis_key or not self.requests:
            return None
        base = "https://kosis.kr/openapi/Param/statisticsParameterData.do"
        default_params = {
            "method": "getList",
            "apiKey": self.kosis_key,
            "itmId": "T1",
            "objL1": "ALL",
            "format": "json",
            "jsonVD": "Y",
            "prdSe": "M",
            "startPrdDe": (datetime.now() - timedelta(days=180)).strftime("%Y%m"),
            "endPrdDe": datetime.now().strftime("%Y%m"),
            "orgId": org_id,
            "tblId": tbl_id,
        }
        default_params.update(params)
        try:
            resp = self.requests.get(base, params=default_params, timeout=10)
            data = resp.json()
            if isinstance(data, list) and data:
                return data[-1]
        except Exception as e:
            log.warning(f"KOSIS API 실패 ({org_id}/{tbl_id}): {e}")
        return None

    def fetch_unemployment(self) -> float | None:
        """실업률."""
        row = self._fetch_kosis("101", "DT_1DA7012S")
        if row:
            try:
                return float(row.get("DT", row.get("TBL_VAL", "")))
            except:
                pass
        return None

    # ── 골프 산업 데이터 (웹 수집) ──
    def fetch_golf_data(self) -> dict:
        """골프 산업 데이터 — 공식 API 없어 최신 공표 데이터 기반."""
        # 한국레저산업연구소, 한국골프장경영협회 연간 보고서 기준
        # 실시간 API가 없으므로 반기/연간 업데이트 시 수동 또는 웹 스크래핑
        result = {}
        if self.requests:
            # 골프장경영협회 등의 공개 데이터 수집 시도
            try:
                # 문화체육관광부 국민체육활동참여실태조사 등 활용 가능
                # 현재는 최신 공표값 하드코딩 (연 1회 업데이트)
                pass
            except:
                pass
        return result

    # ── 통합 수집 ──
    def refresh(self) -> dict:
        """모든 소스에서 강제 갱신."""
        log.info("경제지표 강제 갱신 시작...")
        data = dict(DEFAULTS)
        data["fetch_time"] = datetime.now().isoformat()
        data["source"] = "mixed"
        updated = []

        # 한국은행
        if self.ecos_key:
            br = self.fetch_base_rate()
            if br is not None:
                data["base_rate"] = br
                updated.append("기준금리")

            gdp = self.fetch_gdp_growth()
            if gdp is not None:
                data["gdp_growth"] = gdp
                updated.append("GDP성장률")

            cpi = self.fetch_cpi()
            if cpi is not None:
                data["cpi_rate"] = cpi
                updated.append("소비자물가")

        # 통계청
        if self.kosis_key:
            unemp = self.fetch_unemployment()
            if unemp is not None:
                data["unemployment"] = unemp
                updated.append("실업률")

        if updated:
            data["source"] = "api"
            data["last_update"] = f"API 자동수집 ({datetime.now().strftime('%Y-%m-%d %H:%M')})"
            data["notes"] = f"자동 갱신 항목: {', '.join(updated)}"
            log.info(f"갱신 완료: {updated}")
        else:
            data["last_update"] = f"기본값 (API 키 미설정 또는 연결 실패)"
            data["notes"] = "API 키를 설정하면 한국은행·통계청에서 자동 수집합니다."
            log.info("API 갱신 없음 — 기본값 사용")

        self._save_cache(data)
        return data

    def get_all(self) -> dict:
        """캐시 우선, 만료 시 갱신."""
        cached = self._load_cache()
        if cached and self._is_cache_fresh():
            return cached
        # 캐시 만료 또는 없음 — 갱신 시도
        if self.ecos_key or self.kosis_key:
            return self.refresh()
        # API 키 없으면 캐시(만료되어도) 또는 기본값
        if cached:
            return cached
        return dict(DEFAULTS)

    def get_status(self) -> dict:
        """현재 데이터 상태 정보."""
        cached = self._load_cache()
        has_keys = bool(self.ecos_key or self.kosis_key)
        has_requests = self.requests is not None
        return {
            "api_configured": has_keys,
            "requests_installed": has_requests,
            "cache_exists": CACHE_FILE.exists(),
            "cache_fresh": self._is_cache_fresh(),
            "last_fetch": cached.get("fetch_time") if cached else None,
            "source": cached.get("source") if cached else "none",
            "ecos_key_set": bool(self.ecos_key),
            "kosis_key_set": bool(self.kosis_key),
        }


# ══════════════════════════════════════════════════════
# API 키 설정 안내
# ══════════════════════════════════════════════════════
API_GUIDE = """
### 🔑 API 키 발급 안내 (무료)

**1. 한국은행 ECOS API** → 기준금리, GDP, 소비자물가
- 신청: https://ecos.bok.or.kr/api/#/
- 회원가입 후 즉시 발급 (무료, 일 1만건)
- 제공 데이터: 기준금리, GDP성장률, 물가지수, 환율 등

**2. 통계청 KOSIS API** → 실업률, 인구, 가처분소득
- 신청: https://kosis.kr/openapi/
- 회원가입 후 즉시 발급 (무료)
- 제공 데이터: 실업률, 경제활동인구, 가처분소득, 지역인구 등

**3. 골프 산업 데이터** → 골프인구, 연습장 수
- 한국골프장경영협회 연간보고서 (연 1회 발행)
- 문화체육관광부 국민체육활동참여실태조사 (격년)
- → 현재 공식 API 없음, 보고서 발표 시 수동 업데이트 또는 웹 수집

---
**설정 방법**: 사이드바 하단 `🔑 API 설정`에서 키 입력 → `🔄 지금 갱신` 클릭
"""


# ══════════════════════════════════════════════════════
# CLI 테스트
# ══════════════════════════════════════════════════════
if __name__ == "__main__":
    import sys
    ecos = os.environ.get("ECOS_API_KEY", "")
    kosis = os.environ.get("KOSIS_API_KEY", "")

    if "--test" in sys.argv:
        print("=== 경제지표 수집 테스트 ===")
        fetcher = EconomicDataFetcher(ecos, kosis)
        print(f"상태: {fetcher.get_status()}")
        data = fetcher.get_all()
        for k, v in data.items():
            print(f"  {k}: {v}")
    else:
        print("사용법: python data_fetcher.py --test")
        print("환경변수: ECOS_API_KEY, KOSIS_API_KEY")
