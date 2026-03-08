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
        self.setWindowTitle("예비교사 가이드")
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
        btn_close = QPushButton("닫기")
        btn_close.clicked.connect(self.accept)
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)

    def _build_html(self) -> str:
        return (
            "<h2>GalaCosmo 예비교사 가이드</h2>"
            "<p>GalaCosmo는 공개 천문 데이터(OER)와 GUI 조작을 연결해, "
            "예비교사가 코딩 없이도 암흑물질과 우주론을 탐구할 수 있도록 설계된 학습 도구입니다. "
            "핵심 활동은 SPARC 은하 회전곡선을 해석하며 "
            "가시물질만으로는 설명되지 않는 회전속도 분포를 확인하는 것입니다.</p>"

            "<h3>1) 이 프로그램으로 무엇을 탐구하나요?</h3>"
            "<ul>"
            "<li>관측 회전곡선과 가시물질 기여도를 비교해 암흑물질의 필요성을 설명할 수 있습니다.</li>"
            "<li>M/L(질량-광도비) 조정이 질량 분포 해석에 어떤 영향을 주는지 살펴볼 수 있습니다.</li>"
            "<li>ISO와 NFW 헤일로 모델의 차이를 적합 결과와 잔차로 비교할 수 있습니다.</li>"
            "<li>2D 그래프와 3D 시각화를 연결해 은하 구조를 직관적으로 해석할 수 있습니다.</li>"
            "</ul>"

            "<h3>2) 권장 탐구 순서</h3>"
            "<ol>"
            "<li><b>파일 불러오기</b>: SPARC Table1, Table2를 불러옵니다.</li>"
            "<li><b>은하 선택</b>: 하나의 은하를 고르고, 먼저 Observed와 Baryons를 비교합니다.</li>"
            "<li><b>M/L 조정</b>: Disk와 Bulge의 M/L을 바꾸며 가시물질 곡선이 어떻게 달라지는지 봅니다.</li>"
            "<li><b>헤일로 비교</b>: ISO와 NFW를 번갈아 적용하고 Total 및 Residuals를 비교합니다.</li>"
            "<li><b>3D 보기</b>: 원반, 벌지, 헤일로 구조를 공간적으로 해석합니다.</li>"
            "</ol>"

            "<h3>3) 회전곡선 해석 포인트</h3>"
            "<ul>"
            "<li><b>Observed</b>: 실제 관측 회전속도입니다.</li>"
            "<li><b>Baryons</b>: Disk, Bulge, Gas의 가시물질 합성 곡선입니다.</li>"
            "<li><b>Total</b>: Baryons와 Halo를 함께 고려한 전체 모형 곡선입니다.</li>"
            "<li>외곽부에서 Observed가 Baryons보다 계속 높게 유지되면, 추가 질량 성분의 필요성을 토론할 수 있습니다.</li>"
            "<li>Residuals는 어느 반지름 구간에서 모형이 관측값을 잘 설명하지 못하는지 보여줍니다.</li>"
            "</ul>"

            "<h4>M/L(질량-광도비)와 헤일로 모델</h4>"
            "<ul>"
            "<li>SPARC의 Vdisk, Vbul은 Υ=1 기준으로 제공되며, 앱에서 입력한 M/L로 재스케일됩니다.</li>"
            "<li>문헌에서는 Υ<sub>3.6</sub> ~= 0.5(디스크), 0.7(벌지) 같은 값을 자주 사용합니다.</li>"
            "<li><b>ISO</b>: 중심 코어가 있는 경험적 모델입니다.</li>"
            "<li><b>NFW</b>: 우주론 시뮬레이션에서 자주 등장하는 중심 커스프형 모델입니다.</li>"
            "</ul>"

            "<h3>4) 3D 보기 활용</h3>"
            "<ul>"
            "<li>3D 보기는 Table2의 SBdisk, SBbul 정보를 바탕으로 원반과 벌지 구조를 시각화합니다.</li>"
            "<li>헤일로는 직관적 이해를 돕기 위한 시각화이며, 교육적 해석에 초점을 둡니다.</li>"
            "<li>2D 회전곡선에서 본 질량 분포 차이를 3D 구조와 연결해 설명해 보세요.</li>"
            "</ul>"

            "<h3>5) 수업 또는 세미나 질문 예시</h3>"
            "<ul>"
            "<li>가시물질만으로 회전곡선 외곽부를 설명할 수 있는가?</li>"
            "<li>M/L 값을 바꾸면 암흑물질의 필요성이 얼마나 줄어드는가?</li>"
            "<li>ISO와 NFW 중 어떤 모델이 더 작은 잔차를 보이는가?</li>"
            "<li>실제 수업에서 학생들이 오해할 수 있는 해석 포인트는 무엇인가?</li>"
            "</ul>"

            "<h3>6) 허블 다이어그램 기능</h3>"
            "<p>SN Ia 허블 다이어그램 창은 암흑물질 탐구의 핵심 기능은 아니지만, "
            "같은 프로그램 안에서 데이터 리터러시와 우주론 모델 비교를 확장 활동으로 다룰 수 있게 해줍니다.</p>"
            "<ul>"
            "<li>기준 우주론(Reference)을 정하고 다른 모델과 잔차를 비교할 수 있습니다.</li>"
            "<li>실제 SN Ia 데이터를 통해 관측 자료와 이론 곡선 비교 활동을 설계할 수 있습니다.</li>"
            "</ul>"

            "<h3>References</h3>"
            "<ul>"
            "<li>SPARC 데이터베이스: https://astroweb.cwru.edu/SPARC/</li>"
            "<li>SPARC: Lelli, McGaugh, Schombert 2016, AJ 152, 157.</li>"
            "<li>Halo: Navarro, Frenk, White 1996/1997 (NFW profile).</li>"
            "<li>Pseudo-isothermal core model: Begeman et al. 1991.</li>"
            "<li>Cosmology distances: Hogg 1999, 'Distance measures in cosmology'.</li>"
            "<li>SN Ia Union2.1: Suzuki et al. 2012, ApJ 746, 85.</li>"
            "</ul>"
            "<p><b>유의</b>: 이 프로그램은 교육용 탐구 도구입니다. "
            "논문화나 엄밀한 해석에는 원문 문헌과 데이터 정의를 함께 확인하세요.</p>"
        )
