"""Position-aware editorial synthesis. Counts are facts; prose is a traditional reading.

No birth-date lookup, model call, new calendar constants or event prediction.
All wording is selected from the computed structure and projected through guard.
"""
from collections import Counter
from html import escape
from . import guard
from .constants import HIDDEN, TEN_GOD_GROUP, CHUNG, HAP, ten_god


# Distinguish the ten gods, rather than calling all five group pairs a personality.
GODS = {
    '상관': ('완성된 답에서도 허점을 찾아 고치는 쪽', '설명·비평·설계처럼 기존 답을 더 낫게 만드는 일', '수정할 필요가 없는 대화까지 첨삭하게 되는 것'),
    '식신': ('손에 익힌 것을 반복해 완성도를 쌓는 쪽', '제작·운영처럼 결과물을 꾸준히 내는 일', '익숙한 품질을 지키느라 마감과 투입량을 늘리는 것'),
    '비견': ('내가 납득한 기준으로 직접 결정하는 쪽', '담당 범위와 결정권이 분명한 일', '도움을 받는 것까지 간섭으로 받아들이는 것'),
    '겁재': ('사람과 경쟁 속에서 판을 움직이는 쪽', '협업·협상처럼 사람 사이에서 기회를 만드는 일', '같이 시작한 사람과 기여도·몫을 다르게 계산하는 것'),
    '정재': ('주어진 자원을 계산하고 꾸준히 관리하는 쪽', '예산·정산·운영처럼 누적 결과를 관리하는 일', '작은 손실을 피하려다 필요한 실험까지 미루는 것'),
    '편재': ('자원과 사람을 연결해 기회를 넓히는 쪽', '영업·제휴처럼 여러 기회를 실제 거래로 잇는 일', '벌여 놓은 기회에 비해 회수와 관리가 뒤처지는 것'),
    '정관': ('역할과 약속의 기준부터 세우는 쪽', '검토·관리처럼 책임과 절차가 분명한 일', '평가 기준이 사라지면 내 선택도 멈추는 것'),
    '편관': ('압박이 걸린 문제를 먼저 수습하는 쪽', '기한·책임이 선명한 문제 해결', '급한 일을 해결할수록 더 많은 긴급 업무를 떠맡는 것'),
    '정인': ('이해할 근거와 안정된 바탕부터 확보하는 쪽', '교육·문서화처럼 이해한 것을 체계로 남기는 일', '충분히 알아야 시작할 수 있다는 조건을 계속 늘리는 것'),
    '편인': ('남들이 넘긴 단서를 연결해 다른 답을 찾는 쪽', '분석·탐색처럼 익숙하지 않은 문제를 파고드는 일', '가능성을 계속 열어 두느라 하나의 답을 끝내지 못하는 것'),
}

# Each group has a distinct mechanism in each domain, not six synonyms for advice.
SCENES = {
    '식상': {
        'work': ('결과를 고치는 능력과 일을 끝내는 기준을 따로 잡아야 합니다', '초안을 받으면 빠진 논리나 사용하기 불편한 부분을 찾아 개선안을 내는 역할에 초점을 둡니다. 반대로 이유를 묻지 않고 정해진 답만 반복해야 하는 역할에서는 이 표현력이 마찰로 번역되기 쉽습니다.', '다음 결과물에는 필수 수정 세 개와 이번에는 손대지 않을 항목을 함께 적으세요.'),
        'money': ('만드는 능력과 돈이 남는 구조는 별도입니다', '결과물을 더 좋게 만드는 데 시간을 쓰는 흐름과 가격·수정 횟수·정산을 정하는 흐름을 분리해 읽습니다. 무상 수정이 계속 붙는 일에서는 매출보다 시간당 남는 몫을 먼저 계산할 필요가 있습니다.', '새 작업 한 건에 가격, 포함되는 수정 횟수, 추가 작업의 조건을 시작 전에 적으세요.'),
        'love': ('설명과 해결책이 공감을 대신하는 순간을 봅니다', '상대가 속상한 일을 말했을 때 무엇이 잘못됐는지부터 분석하면, 도우려는 말이 평가처럼 들릴 수 있습니다. 내용이 맞는가와 상대가 그 답을 요청했는가는 다른 문제입니다.', '다음 깊은 대화에서는 해결책을 말하기 전에 들어주길 원하는지 함께 정리하길 원하는지 물으세요.'),
        'people': ('유용한 지적이 사람에 대한 평가로 들리지 않게 해야 합니다', '모임이나 협업에서 불합리한 부분을 먼저 짚는 역할로 읽습니다. 공개된 자리에서 바로 고치려 하면 문제의 당사자는 내용보다 체면에 반응할 수 있습니다.', '다음 피드백은 공개 자리에서 할 말과 일대일로 할 말을 나누세요.'),
        'dir': ('더 배우는 것보다 내놓은 결과로 방향을 좁힐 차례인지 봅니다', '생각을 표현하는 축이 앞선 만큼, 머릿속에서 진로를 완벽하게 고르는 방식보다 작은 결과물을 내고 반응을 비교하는 방식에 무게를 둡니다. 선택지를 계속 늘리면 수정할 대상도 함께 늘어납니다.', '고민하는 두 방향에서 같은 시간을 들여 결과물 하나씩 만들고, 완성까지 걸린 시간과 실제 반응을 비교하세요.'),
        'health': ('몸이 멈춘 뒤에도 머릿속 수정 작업이 이어지는지 봅니다', '생활 리듬에서는 쉬는 시간에도 오늘 한 말이나 미완성 결과를 계속 고치는 장면을 점검합니다. 여기서 말하는 것은 생활 습관이며 신체 상태를 판정하는 해석은 아닙니다.', '일을 끝낼 때 내일 고칠 항목을 세 줄로 남기고, 그날 다시 열지 않을 작업을 정하세요.'),
    },
    '비겁': {
        'work': ('책임만큼 결정권이 있는 자리가 중요합니다', '방법까지 계속 승인받아야 하는 일과 결과에 책임지고 방법은 정할 수 있는 일을 구분합니다. 같은 업무량이라도 후자에서 자기 기준을 쓸 여지가 커집니다.', '맡은 업무 한 건에서 승인받을 결정과 직접 내릴 결정을 문서로 나누세요.'),
        'money': ('공동의 성과와 개인의 몫을 먼저 나눠야 합니다', '친분으로 시작한 협업에서 각자가 들인 시간을 다르게 기억하는 장면을 먼저 봅니다. 관계가 가깝다는 사실이 정산 기준을 대신하지는 않습니다.', '공동 작업 하나의 비용·역할·배분 기준을 시작 전에 합의하세요.'),
        'love': ('함께하는 시간 안에서도 결정권을 남겨 두는 관계를 봅니다', '연락이나 일정을 전부 맞추는 것을 애정의 기준으로 삼으면 자율성과 친밀감이 부딪히기 쉽다고 읽습니다.', '둘이 정할 일정과 각자 정할 일정을 하나씩 구분하세요.'),
        'people': ('경쟁과 협력을 같은 관계에 겹쳐 놓는지 봅니다', '같은 목표로 모였어도 누가 결정하고 누구의 성과로 남는지가 모호하면 비교가 앞설 수 있습니다.', '다음 협업에서 최종 결정자와 각자의 결과물을 미리 정하세요.'),
        'dir': ('남의 성공 방식보다 내가 책임질 조건을 기준으로 삼습니다', '비슷한 사람이 무엇을 선택했는지 계속 비교하면 자신의 조건보다 경쟁의 속도로 결정할 수 있습니다.', '비교 대상의 성과를 빼고 내가 감당할 시간·비용·결정권만 적으세요.'),
        'health': ('직접 처리하는 양이 늘어나는 생활을 점검합니다', '누군가에게 설명하는 시간보다 혼자 끝내는 시간이 짧다는 이유로 모든 일을 가져오는 장면에 초점을 둡니다.', '이번 주 반복 업무 하나의 완료 기준을 적어 다른 사람에게 넘길 수 있는지 확인하세요.'),
    },
    '재성': {
        'work': ('성과를 수치로 확인할 수 있는 역할에 무게를 둡니다', '기여가 실제 매출·비용·운영 결과로 연결되는 일과, 일을 해도 기준이 바뀌는 일을 구분합니다.', '이번 업무의 완료 기준을 결과 수치와 확인 날짜로 합의하세요.'),
        'money': ('수입 규모보다 회수와 유지 비용을 함께 봅니다', '기회가 늘어나는 만큼 자금과 시간도 묶입니다. 계약한 금액, 실제 받은 금액, 유지에 드는 비용을 별도로 볼 필요가 있습니다.', '진행 중인 거래에서 받을 금액·받을 날·추가 비용을 한 줄씩 적으세요.'),
        'love': ('챙겨 준 행동이 말하지 않은 기대를 만드는지 봅니다', '시간과 비용을 들여 돌보는 방식은 구체적이지만, 상대가 원한 배려와 다르면 서로 주고받았다고 느끼는 양이 달라질 수 있습니다.', '최근 해준 일 하나에서 부탁받은 것과 스스로 기대한 보답을 구분하세요.'),
        'people': ('도움과 거래의 경계가 관계의 쟁점입니다', '성과를 함께 만드는 관계에서 상대에게 기대한 기여를 말하지 않으면 실망이 뒤늦게 드러날 수 있습니다.', '다음 부탁이 호의인지 서로 교환할 일인지 먼저 말하세요.'),
        'dir': ('기회마다 필요한 유지 비용을 비교합니다', '겉으로 보이는 보상보다 그 보상을 유지하기 위해 계속 해야 할 일에 초점을 둡니다.', '두 선택의 첫 보상과 석 달 동안 반복할 일을 나란히 적으세요.'),
        'health': ('비워 둔 시간을 손실처럼 취급하는지 봅니다', '빈 시간마다 생산적인 일을 넣으면 일정에는 여유가 있어도 실제로 멈추는 시간은 사라질 수 있습니다.', '이번 주 일정에 결과물을 요구하지 않는 시간을 먼저 남기세요.'),
    },
    '관성': {
        'work': ('평가와 책임의 경계가 업무 만족도를 가릅니다', '책임은 분명하지만 권한과 지원이 빠진 역할에서는 성실하게 해내는 것만으로 부담이 줄지 않습니다.', '추가 업무를 받을 때 기존 업무 중 무엇의 우선순위를 낮출지 함께 정하세요.'),
        'money': ('약속을 유지하기 위한 지출을 따로 봅니다', '직책·관계·체면을 유지하려고 반복하는 비용이 실제 필요와 섞이는 장면을 점검합니다.', '고정 지출 중 내가 원해서 쓰는 것과 역할 때문에 유지하는 것을 나누세요.'),
        'love': ('관계의 안정과 정답을 요구하는 태도를 구분합니다', '약속을 지키는 일은 중요하지만, 정해 둔 방식만 애정으로 인정하면 상대의 다른 표현을 놓칠 수 있습니다.', '지켜야 할 약속 하나와 서로 다르게 해도 되는 부분 하나를 말하세요.'),
        'people': ('거절을 무책임으로 받아들이는 순간을 봅니다', '맡은 일을 끝내려는 기준이 강하면 범위를 넘는 부탁도 역할의 일부로 끌어안을 수 있습니다.', '새 부탁을 받으면 책임 범위에 포함되는지부터 확인하세요.'),
        'dir': ('인정받는 선택과 내가 유지할 선택을 구분합니다', '직함이나 외부 평가가 좋은 선택이라도 그 역할을 매일 유지할 조건은 따로 확인해야 합니다.', '직함을 가리고 실제 하루 일정만 놓고 두 선택을 비교하세요.'),
        'health': ('해야 할 일을 마쳐야 쉴 수 있다는 규칙을 점검합니다', '업무가 끝없이 추가되는 환경에서 완료를 휴식의 전제조건으로 두면 쉬기 시작하는 시각이 계속 밀립니다.', '할 일의 소진과 별개로 오늘 일을 멈출 시각을 정하세요.'),
    },
    '인성': {
        'work': ('이해한 것을 재사용 가능한 체계로 남기는 역할을 봅니다', '자료를 읽고 원리를 연결하는 힘을 문서·교육·분석 결과로 남길 때 준비 시간이 다른 사람에게도 쓰입니다.', '이번에 조사한 내용을 다음 사람이 바로 쓸 한 페이지로 끝내세요.'),
        'money': ('준비에 쓰는 돈과 활용한 결과를 연결해야 합니다', '배움과 도구를 확보하는 일이 실제 사용보다 앞서면 안심을 얻는 소비와 필요한 준비가 섞일 수 있습니다.', '새 자료나 도구를 사기 전에 이미 가진 것 하나로 끝낼 일을 정하세요.'),
        'love': ('충분히 이해한 뒤 말하려다 표현이 늦어지는지 봅니다', '상대의 사정을 여러 방향으로 생각하는 동안 정작 자신의 요청은 전달하지 못하는 장면에 초점을 둡니다.', '상대의 이유를 더 추측하기 전에 지금 원하는 것을 한 문장으로 말하세요.'),
        'people': ('설명하고 돌보는 역할이 한쪽에 쌓이는지 봅니다', '사람들의 사정을 이해해 주는 역할이 반복되면 자신의 요구를 꺼내는 순서가 뒤로 밀릴 수 있습니다.', '다음 부탁을 듣기 전에 오늘 내가 가능한 시간을 먼저 말하세요.'),
        'dir': ('정보가 늘어도 선택 기준이 늘지 않게 해야 합니다', '새 자료를 읽을 때마다 선택 조건을 추가하면 결정을 위한 공부가 결정을 미루는 방식으로 바뀔 수 있습니다.', '추가 조사 전에 결정을 바꿀 사실을 하나로 한정하세요.'),
        'health': ('생각을 정리하는 시간과 실제 쉬는 시간을 나눕니다', '정리와 복기를 휴식으로 여기면 쉬는 시간에도 판단할 일이 계속 남을 수 있습니다.', '하루 마무리 기록은 세 줄로 끝내고 추가 분석은 다음 날로 옮기세요.'),
    },
}

# Unequal pairs must not receive the same causal story in both directions.
# (leading group: title, mechanism, action). Balanced pairs keep the reviewed rule.
PAIR_READINGS = {
    'output_value': {
        '식상': ('품질을 높이는 속도에 정산이 따라오는지 봅니다', '만들고 개선하는 비중이 대가를 확보하는 비중보다 큽니다. 추가 작업이 계약 밖으로 늘어나는 장면을 먼저 읽습니다.', '새 작업의 수정 횟수와 추가 비용을 시작 전에 적어 보세요.'),
        '재성': ('기회를 받는 속도에 제작 여력이 따라오는지 봅니다', '거래와 결과 확보의 비중이 직접 제작하는 비중보다 큽니다. 일을 확보한 뒤 납기와 품질을 감당할 자원이 부족해지는 장면을 먼저 읽습니다.', '새 약속을 받기 전에 기존 작업의 남은 시간과 가능한 납기를 계산해 보세요.'),
    },
    'autonomy_standards': {
        '비겁': ('내 방식으로 결정하기 전에 공동 기준을 고정해야 합니다', '자기 결정의 축이 역할·규칙의 축보다 앞섭니다. 목표에는 동의했어도 방법을 제한받으면 기준 자체를 다시 논의하려는 흐름으로 읽습니다.', '일을 시작할 때 바꿔도 되는 방법과 지켜야 할 기준을 하나씩 합의해 보세요.'),
        '관성': ('맡은 책임에 비해 내 결정권이 작아지는지 봅니다', '역할과 평가의 축이 자기 결정의 축보다 앞섭니다. 승인에 맞추다가 내 판단을 제때 제시하지 못하는 장면을 먼저 읽습니다.', '다음 승인 요청에는 상대의 판단을 묻기 전에 내 권고안을 한 문장으로 적어 보세요.'),
    },
    'pressure_learning': {
        '관성': ('경험이 쌓이기 전에 책임부터 늘어나는 흐름을 봅니다', '책임의 비중이 배움과 지원의 비중보다 큽니다. 급한 일을 반복해서 맡지만 다음에는 덜 힘들게 할 체계가 남지 않는 장면을 먼저 읽습니다.', '반복해서 수습한 문제 하나에 필요한 권한과 지원을 구체적으로 요청해 보세요.'),
        '인성': ('배운 것을 실제 책임으로 옮기는 지점이 필요합니다', '배움과 지원의 비중이 역할의 비중보다 큽니다. 자료와 설명은 충분한데 누가 언제 실행할지 정하지 않는 장면을 먼저 읽습니다.', '이번에 배운 내용 중 내가 책임지고 적용할 한 가지와 완료 날짜를 정해 보세요.'),
    },
    'shared_reward': {
        '비겁': ('같이 시작한 사람의 수보다 나눌 몫을 먼저 봅니다', '사람과 자기 주장의 비중이 자원을 정산하는 비중보다 큽니다. 서로 기여했다고 느끼지만 배분 기준은 늦게 정하는 흐름으로 읽습니다.', '함께할 일의 인원보다 역할별 기여와 배분 기준을 먼저 적어 보세요.'),
        '재성': ('성과를 위해 관계에 요구하는 몫이 커지는지 봅니다', '결과와 자원의 비중이 동료의 축보다 큽니다. 효율을 높이려는 기대가 상대에게는 관계를 평가하는 말로 들릴 수 있다는 해석입니다.', '협업 상대에게 기대하는 결과와 호의로 부탁하는 일을 구분해 보세요.'),
    },
    'expression_rules': {
        '식상': ('개선안의 타당성보다 승인받는 순서가 막힐 수 있습니다', '표현의 비중이 기준과 역할보다 큽니다. 바꿔야 할 이유는 설명했지만 누가 결정하는지 확인하지 않아 의견이 되돌아오는 장면을 먼저 읽습니다.', '다음 수정안에는 바꿀 이유뿐 아니라 승인할 사람과 지킬 기준을 함께 적어 보세요.'),
        '관성': ('틀리지 않으려다 필요한 의견까지 늦추는지 봅니다', '기준과 역할의 비중이 표현보다 큽니다. 규칙에 맞는 답을 찾느라 문제를 알아도 먼저 제안하지 못하는 장면을 읽습니다.', '다음 회의 전에 현재 기준 안에서 시도할 개선안 하나를 준비해 보세요.'),
    },
    'learning_output': {
        '인성': ('이해의 깊이와 내놓는 속도의 간격을 줄여야 합니다', '받아들이고 정리하는 비중이 표현보다 큽니다. 더 알아야 한다는 조건을 늘리는 동안 이미 가진 지식의 쓰임을 시험하지 못하는 흐름으로 읽습니다.', '추가 자료를 찾기 전에 지금 아는 것으로 완성할 한 페이지를 정해 보세요.'),
    },
    'resources_support': {
        '재성': ('이번 성과를 위해 다음 작업의 바탕을 쓰고 있는지 봅니다', '당장 결과를 확보하는 비중이 회복·준비보다 큽니다. 수익이나 성과를 늘리면서 배우고 정비할 시간부터 줄이는 장면을 먼저 읽습니다.', '다음 일을 받을 때 완료 시간과 재정비에 남길 시간을 함께 계산해 보세요.'),
        '인성': ('준비를 확보하는 비용이 실제 활용보다 앞서는지 봅니다', '배움과 보호의 비중이 교환·결과보다 큽니다. 도구나 자료를 늘리는 일이 실행의 필요보다 안심을 얻는 방식이 되는지 읽습니다.', '새 도구를 마련하기 전에 이미 가진 것으로 끝낸 결과를 확인해 보세요.'),
    },
    'reward_responsibility': {
        '재성': ('기회를 넓히기 전에 유지할 약속의 양을 봅니다', '결과와 자원의 비중이 책임의 기준보다 큽니다. 좋은 조건을 먼저 받아들인 뒤 반복 의무를 뒤늦게 확인하는 장면을 읽습니다.', '새 기회에서 일회성 보상과 계속 지켜야 할 약속을 나눠 보세요.'),
        '관성': ('책임을 늘린 만큼 보상 조건도 다시 정해야 합니다', '책임의 비중이 보상과 자원보다 큽니다. 기존 역할을 잘 해냈다는 이유로 추가 역할을 같은 조건에서 맡는 장면을 먼저 읽습니다.', '추가 책임 하나와 그에 필요한 보상·권한을 같은 대화에서 확인해 보세요.'),
    },
    'independent_support': {
        '비겁': ('도움을 받으면서도 결정권을 지킬 방법이 필요합니다', '자기 결정의 비중이 지원보다 큽니다. 맡기면 내 방식이 깨질 것 같아 설명하고 넘기는 일을 미루는 흐름으로 읽습니다.', '다음 도움 요청에서 내가 결정할 부분과 상대가 처리할 작업을 나눠 보세요.'),
        '인성': ('도움을 구하는 것과 결정을 맡기는 것을 구분합니다', '지원과 이해의 비중이 자기 결정보다 큽니다. 조언을 충분히 듣고도 누구의 기준으로 고를지 정하지 못하는 장면을 먼저 읽습니다.', '조언을 더 듣기 전에 내가 책임질 선택 기준 두 가지를 적어 보세요.'),
    },
    'initiative_expression': {
        '비겁': ('먼저 정한 방향을 다른 사람이 이해할 언어로 옮겨야 합니다', '자기 결정의 비중이 표현보다 큽니다. 내 안에서는 결론이 났지만 상대에게 설명한 조건은 부족한 채 함께 움직이길 기대하는 장면을 읽습니다.', '다음 제안에서는 결론과 함께 왜 그 방향인지 핵심 이유를 먼저 설명해 보세요.'),
    },
}


def paragraph(text, css=''):
    return '<p' + (' class="' + css + '"' if css else '') + '>' + escape(text) + '</p>'


def profile(f, facts):
    groups = {g: facts['group:' + g]['value'] for g in SCENES}
    maximum = max(groups.values())
    leaders = [g for g, n in groups.items() if n == maximum]
    counted = [s for g in groups for s in facts['group:' + g]['seats'] if s['position'] != '지장간']
    gods = Counter(s['god'] for s in counted)
    top = max(gods.values())
    dominant_gods = [g for g, n in gods.items() if n == top]
    stems = [s for s in counted if s['position'] == '천간']
    month = next(p for p in f.pillars if p['label'] == '월주')
    day = next(p for p in f.pillars if p['label'] == '일주')
    return dict(groups=groups, leaders=leaders, total=sum(groups.values()), gods=dict(gods),
                dominant_gods=dominant_gods, stems=stems, month=month, day=day,
                month_god=ten_god(HIDDEN[month['ji']][0][0], f.day_gan),
                day_god=ten_god(HIDDEN[day['ji']][0][0], f.day_gan))


def distribution(pr):
    return ' · '.join(f'{g} {n}' for g, n in pr['groups'].items())


def group_evidence(facts, group):
    fact = facts['group:' + group]
    hidden = [s for s in fact['seats'] if s['position'] == '지장간']
    line = fact['label'] + ' — ' + fact['text']
    if hidden:
        line += ' 별도 지장간: ' + ' · '.join(s['pillar'] + ' 속 ' + s['gan'] + '(' + s['god'] + ')' for s in hidden) + '.'
    elif not fact['value']:
        line += ' 지장간에서도 확인되지 않습니다.'
    return line


def portrait_html(f, plan):
    pr = plan['personal']
    html = paragraph('일간 ' + f.day_gan + ' · 월주 ' + pr['month']['gz'] + ' · ' + distribution(pr), 'reading-origin')
    html += paragraph(f"천간과 지지 본기 {pr['total']}자리 중 {'·'.join(pr['leaders'])}이 {max(pr['groups'].values())}자리로 가장 많이 잡힙니다. 지장간의 나머지 글자는 이 개수에 중복해 넣지 않았습니다.")
    for god in pr['dominant_gods']:
        seats = [s for g in SCENES for s in plan['facts']['group:' + g]['seats'] if s['god'] == god and s['position'] != '지장간']
        html += paragraph(god + '이 놓인 곳 · ' + ' · '.join(s['pillar'] + ' ' + s['position'] + ' ' + s['gan'] for s in seats))
    repeated = Counter(s['god'] for s in pr['stems'])
    for god, n in repeated.items():
        if n >= 2:
            html += paragraph(f'{god}이 천간에 {n}번 반복됩니다. 지장간에만 있는 글자와 달리 표현의 축이 바깥에 거듭 드러난 배치로 읽습니다.')
    html += paragraph(f"월지 {pr['month']['ji']}의 본기는 {pr['month_god']}, 일지 {pr['day']['ji']}의 본기는 {pr['day_god']}입니다. 월지의 활동 방식과 일지의 가까운 생활 자리를 구분해 읽습니다.")
    if f.hour_known:
        corrected = f.correction.get('after', '')
        if len(corrected) == 5 and corrected[2] == ':':
            hour, minute = map(int, corrected.split(':'))
            phase = (hour * 60 + minute - 60) % 120
            distance = min(phase, 120 - phase)
            if distance <= 5:
                html += paragraph(f'시주 경계와 가까운 입력 · 보정 시각 {corrected}은 두 시간 단위 시주 경계에서 약 {distance}분 떨어져 있습니다. 출생 도시나 기록된 분이 달라지면 시주와 위의 비중도 바뀔 수 있으므로 이 부분은 입력 조건과 함께 읽어야 합니다.', 'reading-origin')
    if not plan['rejected']:
        for god in pr['dominant_gods']:
            manner, work, friction = GODS[god]
            html += paragraph('전통 해석에서의 중심 · ' + manner + '으로 읽습니다. 쓰임은 ' + work + '에, 마찰은 ' + friction + '에 둡니다.')
        if len(pr['dominant_gods']) > 1:
            html += paragraph('최다 십신이 동률이므로 위의 방식 가운데 하나를 성격의 정답으로 고르지 않습니다.')
        if pr['month_god'] != pr['day_god']:
            html += paragraph('활동과 가까운 생활의 차이 · 밖의 일은 ' + GODS[pr['month_god']][0] + ', 가까운 생활은 ' + GODS[pr['day_god']][0] + '으로 나눠 읽습니다. 같은 사람이 일할 때와 편한 관계에서 요구하는 조건이 달라질 수 있다는 해석입니다.')
    else:
        html += paragraph('경험과 다르다고 답한 해석이 있어 성향을 다른 표현으로 다시 붙이지 않았습니다. 위에는 계산된 배치만 남겼습니다.')
    return guard.enforce(html)


def domain_reading(plan, concern):
    pr, facts = plan['personal'], plan['facts']
    target = {'work': '관성', 'money': '재성', 'love': '인성', 'people': '비겁', 'dir': '식상', 'health': '인성'}[concern]
    html = paragraph(group_evidence(facts, target), 'reading-origin')
    if concern == 'money' and not pr['groups']['재성']:
        html += paragraph('재성 0은 천간·본기 집계의 값입니다. 재산이나 소득이 없다는 뜻이 아닙니다. 표현·제작에서 교환·정산으로 이어지는 과정을 별도로 확인하는 근거로 씁니다.')
    if concern == 'work' and not pr['groups']['관성']:
        html += paragraph('관성이 겉의 집계에 없다는 이유로 직장 생활이 맞지 않는다고 정하지 않습니다. 맡을 역할·평가·승인 기준이 실제로 얼마나 명확한지가 해석을 가르는 조건입니다.')
    if concern == 'love':
        html += paragraph('관계에서 함께 보는 일지 · ' + pr['day']['gz'] + '의 본기는 ' + pr['day_god'] + '입니다. 상대의 성격이나 결혼 결과를 이 글자로 확정하지 않습니다.')
    if plan['rejected']:
        return guard.enforce(html + paragraph('이 영역의 성향 확장은 보류했습니다. 거절한 해석을 영역 이름만 바꿔 다시 제시하지 않습니다.'))
    for group in pr['leaders']:
        title, body, action = SCENES[group][concern]
        html += '<h3>' + escape(title) + '</h3>'
        html += paragraph(f"이 해석을 고른 배치 · {group} {pr['groups'][group]}/{pr['total']}자리. " + body)
        relevant = {god: n for god, n in pr['gods'].items() if TEN_GOD_GROUP[god] == group}
        peak = max(relevant.values())
        for god, count in relevant.items():
            if count == peak:
                html += paragraph(f'{group} 안에서는 {god} {count}자리가 앞섭니다. ' + GODS[god][0] + '이라는 세부 해석을 적용합니다.')
        html += paragraph('구체적으로 바꿀 것 · ' + action, 'reading-action')
    return guard.enforce(html)


def specialize(rule, facts):
    """Relative composition changes the claim, including opposite dominance."""
    result = dict(rule)
    a, b = rule['groups']
    na, nb = (facts['group:' + g]['value'] for g in (a, b))
    result['composition'] = f'{a} {na} · {b} {nb}'
    if na == nb:
        result['thesis'] = f'{a}과 {b}이 각각 {na}자리로 집계됩니다. ' + rule['thesis']
    else:
        lead, tail = (a, b) if na > nb else (b, a)
        result['thesis'] = f'{lead} {max(na, nb)}자리와 {tail} {min(na, nb)}자리의 비대칭을 먼저 읽습니다. ' + rule['thesis']
        variant = PAIR_READINGS.get(rule['id'], {}).get(lead)
        if variant:
            title, mechanism, action = variant
            result.update(title=title, thesis=result['composition'] + '. ' + mechanism, action=action, directional=True,
                          question=f'{lead}의 방식이 {tail}의 방식보다 앞선다는 해석이 최근 경험과 비슷했나요?')
    if rule['id'] == 'learning_output' and facts['group:식상']['value'] > facts['group:인성']['value']:
        result.update(title='준비 부족보다 계속 고치는 과정에서 마감이 밀리는지 봅니다',
            thesis=result['composition'] + '. 받아들이는 축보다 밖으로 내는 축이 많아, 공부만 하다 시작하지 못하는 설명보다 결과를 낸 뒤에도 수정을 멈추지 못하는 쪽에 무게를 둡니다.',
            trigger='초안을 이미 만들었는데 새 생각이 나올 때마다 수정 범위를 넓히는 상황',
            benefit='완료 기준이 고정된 분석·제작에서는 개선점을 실제 결과로 바꾸는 힘으로 읽습니다.',
            cost='추가 수정 시간이 보상되지 않으면 품질은 올라가도 다음 일을 시작할 시간은 줄어듭니다.',
            action='다음 결과물에 완료 조건 세 가지와 이번에 제외할 개선점을 먼저 적어 보세요.',
            question='최근 시작을 못 한 것보다 이미 만든 결과를 계속 수정하느라 마감이 밀린 적이 있나요?',
            exception='수정이 필수 요구 변경 때문이었다면, 개인의 완벽주의로 설명하지 않습니다.')
    if rule['id'] == 'initiative_expression' and facts['group:식상']['value'] > facts['group:비겁']['value']:
        result.update(title='주도권 자체보다 내 생각을 설명하고 고치는 힘이 앞섭니다',
            thesis=result['composition'] + '. 사람을 이끌고 경쟁하는 축보다 말·결과물로 표현하는 축이 큽니다. 이 배치에서 먼저 읽을 것은 리더십보다 설명과 수정의 방식입니다.',
            benefit='복잡한 내용을 풀어 설명하거나 초안의 허점을 고치는 일에서는 이 표현의 반복을 완성도를 높이는 데 쓸 수 있습니다.',
            trigger='의견을 한 번 전한 뒤에도 상대가 납득할 때까지 설명이나 수정안을 덧붙이는 상황',
            cost='설명은 정교해져도 상대가 답할 여지가 줄면 설득이 압박으로 들릴 수 있습니다.',
            action='다음 제안에서는 핵심 이유 하나와 선택지 두 개까지만 말하고 상대의 답을 먼저 받아 보세요.',
            question='최근 설명을 더할수록 상대가 대답하기보다 듣기만 했던 적이 있나요?',
            exception='상대가 자세한 설명을 요청했고 그 범위에서 답했다면, 설명의 양 자체를 문제로 해석하지 않습니다.')
    return result


def transit_reading(f, gan, ji):
    god = ten_god(gan, f.day_gan)
    group = TEN_GOD_GROUP[god]
    from .interpretation import GROUPS
    n = getattr(f, GROUPS[group])
    strongest = max(getattr(f, attr) for attr in GROUPS.values())
    relation = '원국에서 가장 많은 축을 다시 더하는 흐름' if n == strongest else '원국의 겉 집계에 없던 축을 더하는 흐름' if n == 0 else '원국에서 앞선 축과 다른 역할을 더하는 흐름'
    detail = {
        '식상': '만들고 설명할 일이 늘어나는 관점으로 읽습니다. 이미 표현의 비중이 크다면 결과의 개수보다 완료·전달 기준을 먼저 잡습니다.',
        '비겁': '직접 결정할 일과 공동으로 나눌 몫을 다룹니다. 협업 제안은 친분과 별도로 결정권·배분 기준을 확인할 주제입니다.',
        '재성': '결과물을 가격·비용·정산으로 바꾸는 조건을 다룹니다. 돈이 들어온다는 예언이 아니라 무엇을 어떤 조건으로 교환할지의 문제입니다.',
        '관성': '평가·책임·약속의 기준을 다룹니다. 표현이 앞선 원국이라면 잘 만든 결과를 승인 가능한 형식으로 정리하는 문제가 부각됩니다.' if f.sik == strongest else '평가·책임·약속의 기준을 다룹니다. 새 역할에서는 책임뿐 아니라 결정권과 지원 범위를 함께 확인할 주제입니다.',
        '인성': '기록·배움·지원 체계를 다룹니다. 새 공부를 늘리는 것과 이미 한 일을 매뉴얼로 남기는 것 가운데 무엇이 필요한지 구분합니다.',
    }[group]
    text = f'{god}을 원국 {group} {n}자리와 비교하면 {relation}으로 읽습니다. ' + detail
    seats = {'년주': '바깥의 관계와 익숙한 소속', '월주': '일하는 역할과 일상의 기준',
             '일주': '가까운 관계에서 지킬 생활과 약속', '시주': '이후에 남길 결과와 장기 계획'}
    for pillar in f.pillars:
        if CHUNG.get(ji) == pillar['ji']:
            text += f" {ji}와 {pillar['label']} {pillar['ji']}의 충은 {seats[pillar['label']]}에서 기존 방식을 조정할 주제로 읽습니다. 실제 이탈이나 관계 단절을 뜻하지는 않습니다."
        elif HAP.get(ji) == pillar['ji']:
            text += f" {ji}와 {pillar['label']} {pillar['ji']}의 육합은 {seats[pillar['label']]}에 새 조건을 함께 묶어 볼 주제로 읽습니다. 합이 있다는 이유만으로 유리한 결과를 정하지 않습니다."
        elif ji == pillar['ji']:
            text += f" {pillar['label']}의 {ji}가 반복되므로 {seats[pillar['label']]}에서 이미 사용하던 기준을 다시 점검하는 관점입니다."
    return text
