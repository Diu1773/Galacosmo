"""User guide dialog with literature context."""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QWidget, QPushButton,
)


class GuideDialog(QDialog):
    """Guide dialog explaining the UI and references."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Guide")
        self.setMinimumSize(720, 600)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        scroll.setWidget(content)
        content_layout = QVBoxLayout(content)

        guide = QLabel(self._build_html())
        guide.setWordWrap(True)
        guide.setTextFormat(Qt.RichText)
        guide.setOpenExternalLinks(False)
        content_layout.addWidget(guide)
        content_layout.addStretch()

        layout.addWidget(scroll)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)

    def _build_html(self) -> str:
        return (
            "<h2>GalaCosmo 사용자 가이드</h2>"
            "<p>이 앱은 SPARC 회전곡선 데이터와 SN Ia 허블 다이어그램을 이용해 "
            "은하 질량 분해와 우주론 모델을 비교 학습/탐색하는 도구입니다.</p>"

            "<h3>1) Rotation Curve (회전곡선)</h3>"
            "<ul>"
            "<li><b>데이터</b>: SPARC Table1(은하 요약) + Table2(반지름별 회전속도).</li>"
            "<li><b>SPARC 개요</b>: 175개 late-type 은하(나선/불규칙) 표본, "
            "Spitzer 3.6 μm 포토메트리(별질량 분포 추적) + "
            "HI+Hα 회전곡선(중력 퍼텐셜 추적).</li>"
            "<li><b>범위</b>: 별질량(약 5 dex), 표면밝기(>3 dex), 가스 분율까지 폭넓게 포함.</li>"
            "<li><b>Table1</b>: 은하별 1줄 요약(거리, 경사각, 광도, Vflat 등).</li>"
            "<li><b>Table2</b>: 반지름별 Vobs/Vgas/Vdisk/Vbul 성분 곡선.</li>"
            "<li><b>워크플로우</b>: Load Files → Select Galaxy → M/L·Halo 설정 → 곡선 비교.</li>"
            "<li><b>Observed</b>: 관측 회전속도, <b>Baryons</b>: Disk+Bulge+Gas 합성,"
            " <b>Total</b>: Baryons+Halo 합성.</li>"
            "<li><b>Display Curves</b>: 우클릭으로 곡선 색상을 변경할 수 있습니다.</li>"
            "</ul>"

            "<h4>Halo 모델</h4>"
            "<ul>"
            "<li><b>ISO</b>(pseudo-isothermal): 중심 코어가 있는 경험적 모델.</li>"
            "<li><b>NFW</b>: 우주론 시뮬레이션 기반의 커스프(cusp) 모델.</li>"
            "</ul>"
            "<p>ISO 속도식(예): "
            "<span>v(r)=sqrt(4πGρ0 rc^2 [1 - (rc/r) arctan(r/rc)])</span></p>"
            "<p>NFW 속도식은 NFW 프로파일에서 유도된 V200, c 파라미터를 사용합니다.</p>"

            "<h4>M/L(질량-광도비)</h4>"
            "<ul>"
            "<li>Υ는 별질량/광도 비율이며, SPARC는 3.6 μm(별질량 추적)에 대한 값을 씁니다.</li>"
            "<li>SPARC rotmod는 Vdisk/Vbul을 Υ=1 기준으로 제공합니다.</li>"
            "<li>문헌에서는 Υ<sub>3.6</sub> ~= 0.5(디스크), 0.7(벌지) 같은 "
            "고정값을 자주 사용합니다.</li>"
            "<li>다른 Υ로 바꿀 때 속도는 sqrt(Υ)로 스케일됩니다.</li>"
            "<li>앱은 Table2(Υ=1)를 기준으로 사용자가 넣은 M/L로 재스케일합니다.</li>"
            "<li>앱 기본 입력값은 Υ(디스크)=0.5, Υ(벌지)=0.7 입니다.</li>"
            "</ul>"

            "<h3>2) Hubble Diagram (SN Ia)</h3>"
            "<ul>"
            "<li><b>데이터</b>: z, μ, (emu) 컬럼을 가진 SN Ia 데이터 파일.</li>"
            "<li><b>샘플</b>: SCP Union2.1 (LBNL 제공) 테이블을 포함합니다.</li>"
            "<li><b>Reference</b>: 프리셋(H0, Ωm, ΩΛ)으로 계산되는 기준 곡선.</li>"
            "<li><b>Models</b>: 고정 비교 곡선(필요시 Manage Models에서 추가/수정).</li>"
            "<li><b>Residual</b>: Δμ = μ_obs − μ_ref.</li>"
            "</ul>"

            "<h4>우주론 수식(요약)</h4>"
            "<ul>"
            "<li>E(z)=sqrt(Ωm(1+z)^3 + Ωk(1+z)^2 + ΩΛ)</li>"
            "<li>D_L=(1+z)·D_M, μ=5 log10(D_L/Mpc)+25</li>"
            "</ul>"

            "<h3>References (문헌)</h3>"
            "<ul>"
            "<li>SPARC 데이터베이스: https://astroweb.cwru.edu/SPARC/</li>"
            "<li>SPARC: Lelli, McGaugh, Schombert 2016, AJ 152, 157.</li>"
            "<li>Halo: Navarro, Frenk, White 1996/1997 (NFW profile).</li>"
            "<li>Pseudo-isothermal core model: Begeman et al. 1991 (e.g., MNRAS 249, 523).</li>"
            "<li>Cosmology distances: Hogg 1999, 'Distance measures in cosmology'.</li>"
            "<li>SN Ia Union2.1: Suzuki et al. 2012, ApJ 746, 85.</li>"
            "</ul>"
            "<p><b>Note</b>: 교육/탐색 목적의 기본값이며, "
            "정확한 해석에는 문헌과 데이터 정의를 확인하세요.</p>"
        )
