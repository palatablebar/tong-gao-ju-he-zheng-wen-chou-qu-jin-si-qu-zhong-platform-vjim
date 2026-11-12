"""Deterministic demo corpus for dedupwire (batch-plan gb-563 §seed).

12 个新闻主题 → 48 篇通稿，按 3 组规模切分：
  * 3 个大簇（7 篇）、3 个中簇（5 篇）、6 个两篇小簇（三组「公告 / 解读」对，
    公告原文的 6 句在两簇之间共用，形成 3 条跨簇疑似边）。
正文来自固定句库，成员之间的差异只有「追加一句来源说明」或「替换一句」，
因此 MinHash + LSH 的簇结构与疑似边结构可以复现（见 verify_corpus.py）。

本模块只产出纯数据（dict），不 import 任何第三方库，seed 与校验脚本共用。
"""
from datetime import datetime, timedelta

BASE_DAY = datetime(2026, 11, 8, 8, 30)

SOURCES = [
    {
        "name": "三江日报",
        "homepage": "https://www.sanjiangdaily.cn",
        "type": "media",
        "weight": 5,
        "extract_rule_status": "ok",
        "description": "三江传媒集团旗舰日报，本地时政与产业报道主渠道，日更 60 条。",
        "slug": "sanjiangdaily",
    },
    {
        "name": "三江晚报",
        "homepage": "https://www.sjwb.cn",
        "type": "media",
        "weight": 4,
        "extract_rule_status": "ok",
        "description": "都市报，民生与社区稿源，转载率高，正文常带栏目导语。",
        "slug": "sjwb",
    },
    {
        "name": "潮声网",
        "homepage": "https://www.chaosheng.com.cn",
        "type": "media",
        "weight": 3,
        "extract_rule_status": "degraded",
        "description": "区域新闻门户，页面为老模板，正文与评论模块混排，抽取规则待升级。",
        "slug": "chaosheng",
    },
    {
        "name": "省政务发布",
        "homepage": "https://www.zjgov.gov.cn",
        "type": "government",
        "weight": 4,
        "extract_rule_status": "ok",
        "description": "省级政务公开平台，政策原文与公告首发地，转载授权明确。",
        "slug": "zjgov",
    },
    {
        "name": "江北观察",
        "homepage": "https://www.jbobserver.com",
        "type": "selfmedia",
        "weight": 2,
        "extract_rule_status": "pending",
        "description": "财经自媒体，解读稿居多，正文短、配图多，抽取规则尚未验收。",
        "slug": "jbobserver",
    },
]

# 主题：key / 标题 / 体量 / 分类 / 地区 / 首个发布时间偏移（小时）
TOPICS = [
    {
        "key": "waterway",
        "title": "京杭运河二通道全线通航",
        "size": 7,
        "category": "产业",
        "region": "三江市",
        "offset_hours": 0,
        "sentences": [
            "京杭运河二通道三江段昨日实现全线通航，首批十二艘千吨级货船依次通过船闸驶入主航道。",
            "该工程全长二十六点四公里，按三级航道标准建设，设计年通过能力两千八百万吨。",
            "市交通运输局介绍，二通道打通后，城区段老运河的货运压力将下降约四成。",
            "沿线新建三座船闸和两处锚泊服务区，船舶待闸时间由平均六小时压缩至两小时以内。",
            "三江港务集团测算，水运成本每吨公里可降低三分钱，一年可为本地企业节省物流费用近亿元。",
            "施工方中铁十二局表示，跨河桥梁全部采用一跨过河方案，避免桥墩占用通航水域。",
            "航道配套的智慧调度系统同步启用，可对船舶位置、闸室水位和待闸队列实时监测。",
            "市港航中心提醒，试运行期间夜间暂不放行危化品船舶，具体时段以航行通告为准。",
        ],
        "variants": [],
    },
    {
        "key": "park",
        "title": "三江新区智能制造产业园开工",
        "size": 7,
        "category": "财经",
        "region": "三江新区",
        "offset_hours": 2,
        "sentences": [
            "三江新区智能制造产业园一期项目昨日正式开工，总投资五十八亿元，占地四百二十亩。",
            "园区规划智能装备、工业机器人和精密零部件三个主导方向，首批入驻企业二十一家。",
            "新区管委会负责人表示，园区达产后预计年产值一百二十亿元，提供就业岗位六千个。",
            "项目由市城投集团与三家社会资本联合出资，采用标准厂房加定制厂房的混合模式。",
            "园区同步建设工业互联网平台，为入驻企业提供设备上云、能耗监测和订单协同服务。",
            "国开行三江分行提供三十亿元授信，前三年按优惠利率执行，支持企业设备购置。",
            "施工方计划明年六月完成主体结构封顶，九月首批厂房交付使用。",
            "新区经发局提示，意向入驻企业可在线提交预审材料，首批审核截止到本月底。",
        ],
        "variants": [],
    },
    {
        "key": "gas",
        "title": "省里下达冬季天然气保供方案",
        "size": 7,
        "category": "民生",
        "region": "三江省",
        "offset_hours": 4,
        "sentences": [
            "省发展改革委昨日下达冬季天然气保供方案，明确今冬明春民生用气优先保障顺序。",
            "方案要求各地签订天然气购销合同，城燃企业储气能力不低于年用气量的百分之六。",
            "省管网公司将在十一月十五日前完成两座储气库注气任务，形成约四亿立方米调峰能力。",
            "对居民、学校、医院和养老机构用气，任何情况下不得压减或限供。",
            "工业用户按可中断、可调节、可转移三类排序，参与调峰的用气价格可下浮百分之五。",
            "方案明确建立日监测、周调度、月通报机制，各市须在每日十七时前报送供需数据。",
            "省能源局将派出现场督导组，重点检查城燃企业储气设施和应急抢修队伍落实情况。",
            "省里提醒，若出现极端天气导致供应紧张，将按预案启动压非保民措施。",
        ],
        "variants": [],
    },
    {
        "key": "metro",
        "title": "江城地铁四号线首列车下线",
        "size": 5,
        "category": "产业",
        "region": "江城市",
        "offset_hours": 7,
        "sentences": [
            "江城地铁四号线首列车昨日在轨道交通装备基地下线，车体采用铝合金焊接结构，最高时速八十公里。",
            "四号线全长二十九公里，设站二十一座，串联老城区、科创园和临港片区三个组团。",
            "列车配置全自动运行系统，可按计划实现自动出库、自动折返和自动调整运行间隔。",
            "车厢内设置动态电子地图和冷暖分区座椅，高峰期额定载客量为一千四百六十人。",
            "市轨道集团表示，四号线将于明年初进入联调联试，年底前具备开通试运营条件。",
            "车内空气净化装置完成升级，可在十分钟内将客室颗粒物浓度降低到优良水平。",
            "市轨道集团提示，沿线七个站点同步实施出入口改造，施工期间部分道路将临时占道。",
            "四号线开通后，预计日客流二十五万人次，沿线公交换乘站点将同步优化。",
        ],
        "variants": [],
    },
    {
        "key": "medical",
        "title": "医保门诊共济政策落地",
        "size": 5,
        "category": "政策",
        "region": "三江市",
        "offset_hours": 9,
        "sentences": [
            "三江市职工医保门诊共济保障政策自本月起正式落地，普通门诊费用纳入统筹基金支付。",
            "在职职工年度起付线为八百元，退休人员为五百元，超出部分按百分之五十至六十比例报销。",
            "政策明确门诊共济的年度支付限额为在职人员六千元，退休人员八千元。",
            "个人账户划入额度同步调整，单位缴费部分不再划入个人账户。",
            "市医保局表示，个人账户可共济给配偶、父母和子女，用于定点机构就医购药。",
            "参保人员可在市域内任意定点机构门诊结算，无需再办理转诊备案手续。",
            "异地门诊直接结算范围扩大至二十八个省份，备案后可在就医地直接结算。",
            "市医保局提醒，年底前将完成定点机构系统升级，期间可能出现短暂结算延迟。",
        ],
        "variants": [],
    },
    {
        "key": "bridge",
        "title": "跨海大桥主塔封顶",
        "size": 5,
        "category": "产业",
        "region": "临港新区",
        "offset_hours": 11,
        "sentences": [
            "三江湾跨海大桥主塔昨日封顶，塔高二百六十八米，为省内最高海上斜拉桥主塔。",
            "大桥全长十四点二公里，主跨八百六十米，双向六车道，设计时速一百公里。",
            "项目建设单位介绍，主塔施工采用爬模工艺，单节段浇筑高度四点五米，共完成五十八节。",
            "海上施工克服季风和潮汐影响，累计投入大型船机设备三十六台套。",
            "大桥计划明年五月合龙，明年底具备通车条件，届时南北两岸通行时间缩短四十分钟。",
            "项目同步建设桥梁健康监测系统，布设传感器一千二百个，实时监测应力与变形。",
            "沿线设置两处观景平台和一处应急救援码头，满足养护与突发事件处置需求。",
            "海事部门提醒，施工水域仍实行临时交通管制，过往船舶须按通告航路行驶。",
        ],
        "variants": [],
    },
]

# 三组「政策公告 / 媒体解读」对：每组 2 个两篇簇，共用 6 句公告原文
PAIRS = [
    {
        "key": "coldchain",
        "labels": ["冷链物流补助细则发布", "冷链补助新政解读"],
        "titles_a": ["我市出台冷链物流补助细则", "冷链物流补助细则 单个项目最高八百万元"],
        "titles_b": ["解读：冷链补助新政落地", "冷链补助新政如何申报 专家划重点"],
        "category": "政策",
        "region": "三江市",
        "offset_hours": 13,
        "shared": [
            "为加快补齐城乡冷链物流短板，经市政府同意，现将有关事项通知如下。",
            "支持对象为在本市注册、具有独立法人资格的冷链物流企业和农产品批发市场。",
            "对新建或改扩建冷库项目，按新增库容每立方米一百二十元给予一次性补助。",
            "申报材料包括项目备案文件、土地证明、投资审计报告和设备采购合同。",
            "各区县发展改革部门负责初审，市发展改革委于每季度末集中复核并公示。",
            "本通知自二零二六年十二月一日起施行，有效期三年。",
        ],
        "unique_a": [
            "市发展改革委昨日发布冷链物流扶持细则，单个项目最高可获八百万元补助。",
            "业内人士认为，补助将推动本地冷库容量在三年内增长三成以上。",
        ],
        "unique_b": [
            "解读：冷链补助新政落地，生鲜电商和医药冷链企业最受益。",
            "专家提醒，申报企业须注意投资审计报告须由具备资质的会计师事务所出具。",
        ],
        "tail_a": "记者在采访中了解到，多家冷链企业已启动前期选址工作，部分项目计划在明年一季度开工，相关进展本报将继续跟踪报道，读者可关注后续版面与本端专题栏目。",
        "tail_b": "多位受访企业负责人表示，补助资金到位节奏直接影响冷库建设进度，建议申报前先与属地发展改革部门沟通确认口径，避免材料反复补正。",
    },
    {
        "key": "charging",
        "labels": ["充电设施补贴通知发布", "充电补贴政策解读"],
        "titles_a": ["省里发文支持新能源汽车充电设施建设", "充电设施补贴通知印发 单桩最高补两万元"],
        "titles_b": ["解读：充电补贴向高速服务区倾斜", "充电补贴申报指南 五类主体可申请"],
        "category": "政策",
        "region": "三江省",
        "offset_hours": 15,
        "shared": [
            "为完善新能源汽车充电基础设施网络，经省政府同意，现就补贴事项通知如下。",
            "补贴范围包括公共充电站、高速公路服务区充电桩和换电站三类设施。",
            "对新建直流快充桩按功率给予补贴，单桩最高不超过两万元。",
            "申报主体须为在本省注册的充电设施运营企业，且接入省级监管平台。",
            "省能源局会同省财政厅组织专家评审，评审结果在门户网站公示五个工作日。",
            "本通知自印发之日起执行，补贴资金按年度预算规模分批次下达。",
        ],
        "unique_a": [
            "省能源局昨日印发充电设施补贴通知，高速公路服务区新建快充桩补贴上浮两成。",
            "截至上月底，全省公共充电桩保有量已达八点六万台，车桩比降至二点一比一。",
        ],
        "unique_b": [
            "解读：充电补贴政策向高速服务区和县域补短板倾斜，运营企业迎来利好。",
            "业内人士测算，按新标准单个高速服务区充电站可获补贴四十万元以上。",
        ],
        "tail_a": "多家充电运营企业向记者反馈，高速服务区点位竞争激烈，企业更关注电网增容、场地租期与平台接入成本，后续政策落地节奏仍需持续观察。",
        "tail_b": "省能源局相关处室负责人表示，评审将侧重设施利用率与监管平台接入质量，单纯追求数量的申报方案通过率不高，企业应提前做好运营数据准备。",
    },
    {
        "key": "air",
        "labels": ["秋冬季大气治理公告发布", "大气治理公告解读"],
        "titles_a": ["市生态环境局发布秋冬季大气治理公告", "秋冬季大气治理公告 涉六类行业"],
        "titles_b": ["解读：大气治理公告对钢构企业影响几何", "大气治理公告十问十答"],
        "category": "民生",
        "region": "三江市",
        "offset_hours": 17,
        "shared": [
            "为持续改善秋冬季环境空气质量，依据大气污染防治法有关规定，现将有关事项公告如下。",
            "公告实施范围为全市行政区域，重点管控行业包括钢铁、建材、化工、铸造、包装印刷和工业涂装。",
            "列入绩效分级 A 级的企业可自主采取减排措施，B 级及以下企业按清单执行停限产。",
            "各企业须在十一月十日前完成一轮废气治理设施自查，并向属地生态环境分局报备。",
            "市生态环境局将组织交叉执法检查，对超标排放企业依法查处并公开曝光。",
            "公告自发布之日起施行，管控措施视空气质量形势动态调整。",
        ],
        "unique_a": [
            "市生态环境局昨日发布秋冬季大气治理公告，六类重点行业纳入差异化管控。",
            "公告首次明确 A 级企业自主减排、B 级及以下企业按清单停限产的分级规则。",
        ],
        "unique_b": [
            "解读：大气治理公告落地后，钢构与工业涂装企业需重点核查废气收集率。",
            "环保专家建议企业提前准备治理设施运行台账，避免交叉执法检查中被认定超标。",
        ],
        "tail_a": "几家重点行业企业负责人表示，分级管控对生产排程影响有限，企业更担心交叉执法口径不一致，目前已安排专人对接属地分局，并按要求提前报送自查报告。",
        "tail_b": "生态环境部门表示，交叉检查将采取四不两直方式，对屡查屡犯企业依法从严处理，检查结果按月在门户网站公开，企业可通过监管平台查询自身评级。",
    },
]

# 大/中簇成员追加的短句（20~25 字），跨文章复用，对整体相似度贡献很小
SHORT_TAILS = [
    "（本文图片由受访单位提供）",
    "更多现场视频请关注三江日报客户端专题。",
    "（记者 林舟 通讯员 周予安）",
    "本稿数据由市港航中心提供，仅供读者参考。",
    "编辑：沈知微 审核：顾砚舟",
    "（本报综合报道）",
    "相关阅读：三江港总体规划全文发布。",
    "本端将持续更新，敬请关注后续追踪。",
]

# 公告对第二篇成员追加的长句（约 90 字），每句独立，避免额外相似
LONG_TAILS = [
    "记者在采访中了解到，多家冷链企业已启动前期选址工作，部分项目计划在明年一季度开工，相关进展本报将继续跟踪报道，读者可关注后续版面与本端专题。",
    "多家充电运营企业向记者反馈，高速服务区点位竞争激烈，企业更关注电网增容与场地租期，后续政策落地节奏仍需观察。",
    "几家重点行业企业负责人表示，分级管控对生产排程影响有限，企业更担心交叉执法口径不一致，已安排专人对接属地分局。",
    "据市发展改革委介绍，申报窗口将在每季度末集中开启，企业可提前准备审计报告和采购合同，避免因材料不全被退回。",
    "省能源局相关处室负责人表示，评审将侧重设施利用率和平台接入质量，单纯追求数量的申报方案通过率不高。",
    "生态环境部门表示，交叉检查将采取四不两直方式，对屡查屡犯企业依法从严处理，检查结果按月在门户网站公开。",
]

EVENTS = [
    {
        "topic_key": "waterway",
        "title": "京杭运河二通道三江段全线通航",
        "category": "产业",
        "event_date": "2026-11-08",
        "region": "三江市",
        "note": "首批千吨级货船通过船闸，老运河货运压力预计下降四成。",
    },
    {
        "topic_key": "park",
        "title": "三江新区智能制造产业园一期开工",
        "category": "财经",
        "event_date": "2026-11-08",
        "region": "三江新区",
        "note": "总投资五十八亿元，首批二十一家企业入驻，达产后年产值一百二十亿元。",
    },
    {
        "topic_key": "gas",
        "title": "省里下达冬季天然气保供方案",
        "category": "民生",
        "event_date": "2026-11-10",
        "region": "三江省",
        "note": "民生用气优先，城燃企业储气能力须达年用气量百分之六。",
    },
    {
        "topic_key": "coldchain",
        "title": "冷链物流补助细则发布",
        "category": "政策",
        "event_date": "2026-11-10",
        "region": "三江市",
        "note": "单项目最高补助八百万元，十二月一日起施行，有效期三年。",
    },
    {
        "topic_key": "charging",
        "title": "充电设施补贴通知印发",
        "category": "政策",
        "event_date": "2026-11-10",
        "region": "三江省",
        "note": "直流快充单桩最高补两万元，高速服务区补贴上浮两成。",
    },
    {
        "topic_key": "air",
        "title": "秋冬季大气治理公告发布",
        "category": "民生",
        "event_date": "2026-11-10",
        "region": "三江市",
        "note": "六类重点行业差异化管控，A 级企业可自主减排。",
    },
]

AUTHORS = ["林舟", "周予安", "沈知微", "顾砚舟", "陈默", "许知远", "苏晚", "程野"]
MEMBER_TITLE_SUFFIX = ["", "（组图）", "｜现场", "（附视频）", " 最新进展", "（快讯）", " 追踪"]
EDITORS = ["顾砚舟", "沈知微", "周予安"]

# 额外 12 条原始条目：6 条采集失败 + 6 条待解析，raws=60 / articles=48
EXTRA_RAWS = [
    ("省政务发布", "关于公布2026年第二批绿色工厂名单的通知", "failed", "HTTP 403：目标站点启用访问校验"),
    ("潮声网", "三江港前十月集装箱吞吐量同比增长百分之九", "failed", "正文节点定位失败：模板变更"),
    ("江北观察", "四季度消费市场观察：以旧换新拉动明显", "failed", "页面重定向超过 5 次"),
    ("三江晚报", "城区新增三处口袋公园 本月底开放", "failed", "连接超时（30s）"),
    ("省政务发布", "关于调整公办幼儿园收费标准的公示", "failed", "证书校验失败：站点证书已过期"),
    ("潮声网", "社区食堂扩面提质 今年新增十二家", "failed", "页面返回空正文（JS 渲染）"),
    ("三江日报", "我市启动冬季消防隐患集中排查", "new", ""),
    ("三江晚报", "地铁四号线沿线公交接驳方案征求意见", "new", ""),
    ("江北观察", "新能源车险费率调整 车主保费有何变化", "new", ""),
    ("省政务发布", "关于公开征求数据要素市场培育意见的公告", "new", ""),
    ("潮声网", "老街改造二期完成 首批商户本月底入驻", "new", ""),
    ("三江日报", "市图书馆启动夜间延时开放试运行", "new", ""),
]

NAV_HTML = (
    '<div class="site-nav"><a href="/">首页</a><a href="/news/">新闻</a>'
    '<a href="/video/">视频</a><a href="/service/">服务</a><a href="/login">登录</a></div>'
)
FOOTER_HTML = (
    '<div class="footer"><p>版权所有 2026 三江传媒集团 互联网新闻信息服务许可证 33120260001</p>'
    '<p><a href="/about">关于我们</a> <a href="/contact">联系方式</a> <a href="/sitemap">网站地图</a></p></div>'
)


def _published(base_hours: int, member_index: int) -> datetime:
    """成员发布时间：第 0 篇最早，后续每篇间隔 40~70 分钟。"""
    return BASE_DAY + timedelta(hours=base_hours, minutes=member_index * 50)


def _date_text(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%d %H:%M")


def _render_article_html(title: str, source: dict, moment: datetime, author: str, paragraphs: list[str]) -> str:
    body = "".join(f"<p>{text}</p>" for text in paragraphs)
    return (
        "<!DOCTYPE html><html><head><meta charset=\"utf-8\">"
        f"<title>{title} - {source['name']}</title></head><body>"
        f"{NAV_HTML}"
        '<div class="crumb">首页 &gt; 新闻 &gt; 正文</div>'
        f"<h1>{title}</h1>"
        f'<div class="meta">{_date_text(moment)}　来源：{source["name"]}　作者：{author}</div>'
        f'<article class="art-body">{body}</article>'
        '<div class="share-box"><a href="#">分享到微信</a><a href="#">分享到微博</a></div>'
        f"{FOOTER_HTML}</body></html>"
    )


def _render_low_conf_summary_html(title: str, source: dict, moment: datetime, author: str,
                                  paragraphs: list[str], summary: str) -> str:
    """低置信 #1：摘要块得分最高但正文过短，触发 fallback 合并全部 <p>。"""
    body = "".join(f"<p>{text}</p>" for text in paragraphs)
    return (
        "<!DOCTYPE html><html><head><meta charset=\"utf-8\">"
        f"<title>{title} - {source['name']}</title></head><body>"
        f"{NAV_HTML}"
        f"<h1>{title}</h1>"
        f'<div class="summary"><p>{summary}</p></div>'
        f'<div class="meta">{_date_text(moment)}　作者：{author}</div>'
        f"{body}"
        f"{FOOTER_HTML}</body></html>"
    )


def _render_low_conf_comment_html(title: str, source: dict, moment: datetime, author: str,
                                  paragraphs: list[str], lead: str) -> str:
    """低置信 #2：正文包在被判为评论模块的容器里，得分低 → fallback。"""
    body = "".join(f"<p>{text}</p>" for text in paragraphs)
    return (
        "<!DOCTYPE html><html><head><meta charset=\"utf-8\">"
        f"<title>{title} - {source['name']}</title></head><body>"
        f"{NAV_HTML}"
        f"<h1>{title}</h1>"
        '<div class="comment-body">'
        f"<p>{lead}</p>{body}"
        "</div>"
        f"{FOOTER_HTML}</body></html>"
    )


LOW_CONF_1 = ("waterway", 3, "【摘要】二通道通航将缓解城区货运压力，水运成本下降、待闸时间压缩、港区联动进一步增强。")
LOW_CONF_1_SUMMARY = LOW_CONF_1[2]
LOW_CONF_2 = ("medical", 2)
LOW_CONF_2_LEAD = "导读：本稿关注医保门诊共济落地进展，涉及起付线、报销比例、异地结算三个方面。"


def build_articles() -> list[dict]:
    """Return every article member with its raw HTML + cluster assignment."""
    articles: list[dict] = []
    cluster_index = 0
    for topic in TOPICS:
        base_hours = topic["offset_hours"]
        for member in range(topic["size"]):
            sentences = list(topic["sentences"])
            if member > 0:
                sentences.append(SHORT_TAILS[(cluster_index * 3 + member) % len(SHORT_TAILS)])
            source = SOURCES[member % len(SOURCES)]
            moment = _published(base_hours, member)
            title = topic["title"] + MEMBER_TITLE_SUFFIX[member % len(MEMBER_TITLE_SUFFIX)]
            author = AUTHORS[(cluster_index + member) % len(AUTHORS)]
            key = f"{topic['key']}-{member + 1}"
            slug = f"{topic['key']}-{member + 1}"
            if (topic["key"], member) == LOW_CONF_1[:2]:
                html = _render_low_conf_summary_html(
                    title, source, moment, author, sentences, LOW_CONF_1_SUMMARY
                )
            elif (topic["key"], member) == LOW_CONF_2:
                html = _render_low_conf_comment_html(
                    title, source, moment, author, sentences, LOW_CONF_2_LEAD
                )
            else:
                html = _render_article_html(title, source, moment, author, sentences)
            articles.append(
                {
                    "key": key,
                    "cluster_index": cluster_index,
                    "cluster_label": topic["title"],
                    "member_index": member,
                    "title": title,
                    "url": f"https://{source['slug']}.cn/news/202611/{slug}.html",
                    "source_slug": source["slug"],
                    "source_index": member % len(SOURCES),
                    "published_at": moment,
                    "author": author,
                    "html": html,
                    "low_confidence": (topic["key"], member) in (LOW_CONF_1[:2], LOW_CONF_2),
                }
            )
        cluster_index += 1

    for pair in PAIRS:
        for side, (labels, titles, unique_key) in enumerate(
            ((pair["labels"], pair["titles_a"], "unique_a"),
             (pair["labels"], pair["titles_b"], "unique_b"))
        ):
            for member in range(2):
                sentences = list(pair["shared"]) + list(pair[unique_key])
                if member == 1:
                    sentences.append(pair["tail_a" if side == 0 else "tail_b"])
                source = SOURCES[(len(articles)) % len(SOURCES)]
                moment = _published(pair["offset_hours"], side * 2 + member)
                title = titles[member]
                author = AUTHORS[(len(articles) + member) % len(AUTHORS)]
                html = _render_article_html(title, source, moment, author, sentences)
                articles.append(
                    {
                        "key": f"{pair['key']}-{'ab'[side]}{member + 1}",
                        "cluster_index": cluster_index,
                        "cluster_label": labels[side],
                        "member_index": member,
                        "title": title,
                        "url": f"https://{source['slug']}.cn/news/202611/{pair['key']}-{'ab'[side]}{member + 1}.html",
                        "source_slug": source["slug"],
                        "source_index": len(articles) % len(SOURCES),
                        "published_at": moment,
                        "author": author,
                        "html": html,
                        "low_confidence": False,
                        "pair_key": pair["key"],
                        "pair_side": side,
                    }
                )
            cluster_index += 1
    return articles


def build_clusters() -> list[dict]:
    """Cluster plan: label + member keys + representative key (member 0)."""
    articles = build_articles()
    clusters: list[dict] = []
    by_label: dict[int, list[dict]] = {}
    for item in articles:
        by_label.setdefault(item["cluster_index"], []).append(item)
    for idx in sorted(by_label):
        members = by_label[idx]
        clusters.append(
            {
                "cluster_index": idx,
                "label": members[0]["cluster_label"],
                "member_keys": [m["key"] for m in members],
                "rep_key": members[0]["key"],
                "first_seen_at": min(m["published_at"] for m in members),
            }
        )
    return clusters


def suspected_pairs() -> list[tuple[str, str]]:
    """设计上应被算法判为「疑似边」的 3 对（跨簇，公告原文共用）。"""
    pairs: list[tuple[str, str]] = []
    for pair in PAIRS:
        pairs.append((f"{pair['key']}-a1", f"{pair['key']}-b1"))
    return pairs


def extra_raws() -> list[dict]:
    """12 条未产出 Article 的原始条目（6 failed + 6 new），补齐 raws=60。"""
    rows = []
    base = BASE_DAY + timedelta(hours=20)
    for idx, (source_name, title, status, note) in enumerate(EXTRA_RAWS):
        source = next(s for s in SOURCES if s["name"] == source_name)
        moment = base + timedelta(minutes=idx * 35)
        rows.append(
            {
                "source_slug": source["slug"],
                "url": f"https://{source['slug']}.cn/news/202611/extra-{idx + 1}.html",
                "title": title,
                "published_at": moment,
                "status": status,
                "error_note": note,
                "html": (
                    "<!DOCTYPE html><html><head><meta charset=\"utf-8\">"
                    f"<title>{title} - {source['name']}</title></head><body>"
                    f"{NAV_HTML}<h1>{title}</h1><p>{note or '待解析正文'}</p>{FOOTER_HTML}</body></html>"
                ),
            }
        )
    return rows
