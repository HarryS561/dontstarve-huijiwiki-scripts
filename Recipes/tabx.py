from constants import DST_VERSION


# Exceptions
class BlankValueError(Exception):
    def __init__(self, message="该字段不能为空"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"BlankValueError: {self.message}"


class TabxInitError(Exception):
    def __init__(self, message="tabx实例错误"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"TabxInitError: {self.message}"


class FieldValidationError(Exception):
    def __init__(self, message="字段错误"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"FieldValidationError: {self.message}"


# Manager
class Manager:

    def __init__(self):
        self.binding = False
        self.datas = []

    def bind_to_tabx(self, cls):
        self.tabx = cls
        self.binding = True

    def to_list(self):
        res = []
        for data in self.datas:
            res.append(list(data.values()))
        return res

    def clear(self):
        self.datas.clear()


# Fields
class Field:
    _type = None

    def __init__(
        self,
        name=None,
        null=True,
        blank=False,
        en=None,
        zh=None,
        primary_key=False,
        **kwargs,
    ):
        """
        Parameters:
            name (str): 字段名，空缺则为属性名
            null (bool): 是否允许为空值None，这会在valdate中检验
            blank (bool): 初始化时是否允许不填值,若允许，则将该值填为None
            en (str): 字段的英文名，默认等同name
            zh (str): 字段的中文名
            primary_key (bool): 该字段是否作为表的主键
        """
        self.name = name
        self.null = null
        self.blank = blank
        self.name_en = en or name
        self.name_cn = zh
        self.pk = primary_key

    def __str__(self):
        return f"Field:{self.name}"

    def __repr__(self) -> str:
        return f"<Field: {self.name}>"

    def to_dict(self):
        return {
            "name": self.name,
            "type": self._type,
            "title": {"en": self.name_en, "zh": self.name_cn},
        }


class StringField(Field):
    _type = "string"

    def validate(self, value):
        if value is None:
            if self.null is False:
                raise FieldValidationError(
                    f"值为None但是{self.name}字段不能为空"
                )
        elif not isinstance(value, str):
            raise FieldValidationError(
                f"值类型为{type(value)}但是{self.name}字段应该是字符串"
            )


class NumberField(Field):
    _type = "number"

    def validate(self, value):
        if value is None:
            if self.null is False:
                raise FieldValidationError(
                    f"值为None但是{self.name}字段不能为空"
                )
        elif not isinstance(value, (float, int)):
            raise FieldValidationError(
                f"值类型为{type(value)}但是{self.name}字段应该是数字"
            )


class BooleanField(Field):
    _type = "boolean"

    def validate(self, value):
        if value is None:
            if self.null is False:
                raise FieldValidationError(
                    f"值为None但是{self.name}字段不能为空"
                )
        elif not isinstance(value, bool):
            raise FieldValidationError(
                f"值类型为{type(value)}但是{self.name}字段应该是布尔"
            )


# Meta for Tabx
class MetaTabx(type):
    def __init__(self, name, bases, dct):
        super().__init__(name, bases, dct)
        if hasattr(self, "fields"):
            self.init()


# Tabxes
class Tabx(metaclass=MetaTabx):
    """
    tabx表的基类，继承并定义字段及fields后成为实际的类，
    一个实例对应表中的一行，
    整表的操作是通过objects属性所指向的Manager来完成的。
    """

    license = "CC0-1.0"
    _sources = "Extract data from patch {}"
    _description = "尚未填写表的描述"

    @classmethod
    def init(cls):
        """
        初始化cls.fields对象储存并检验相应的字段定义
        并构造一个objects指向所属类的属性objects.tabx
        每个子类都会在定义完自动运行该类方法
        """
        if not cls.fields:
            pk = False
            for name, field in cls.__dict__.items():
                if isinstance(field, Field):
                    name = name.strip("_")
                    if field.pk and not pk:
                        pk = field.name
                    elif field.pk and pk:
                        raise TabxInitError(
                            f"多个字段:{pk},{field.name}定义为主键"
                        )
                    cls.fields[name] = field
                    if field.name is None:
                        field.name = name
                    if field.name_en is None:
                        field.name_en = field.name
                    if field.name_cn is None:
                        field.name_cn = ""
        objects = getattr(cls, "objects", None)
        if objects and not objects.binding:
            objects.bind_to_tabx(cls)

    def __init__(self, *args, **kwargs):
        for name, field in self.fields.items():
            if name in kwargs:
                setattr(self, name, kwargs.pop(name))
            elif not field.blank:
                # 不允许为空值
                raise BlankValueError(f"{name}字段不能为空")
            else:
                setattr(self, name, None)
        if kwargs:
            raise TabxInitError(f"传入了多余的参数: {list(kwargs.keys())}")

    def pre_save(self):
        # 预留钩子
        pass

    def post_save(self):
        # 预留钩子
        pass

    def save(self):
        self.pre_save()
        self.validate()
        for field_name, field in self.fields.items():
            # tabx不允许字符串有前后空格
            if isinstance(field, StringField):
                val = getattr(self, field_name)
                if val and val.strip() != val:
                    setattr(self, field_name, val.strip())
        self.objects.datas.append(self)
        self.post_save()

    def validate(self):
        for name, field in self.fields.items():
            field.validate(getattr(self, name))

    def values(self):
        for field in self.fields:
            yield getattr(self, field)

    @classmethod
    def export(cls):
        """返回包含表头在内的字典"""
        res = {}
        res["license"] = cls.license
        res["description"] = {"zh": cls._description}
        res["sources"] = cls._sources.format(DST_VERSION or "未知版本")
        res["schema"] = schema = {}
        fields = schema["fields"] = []
        for field in cls.fields.values():
            fields.append(field.to_dict())
        res["data"] = cls.objects.to_list()
        return res

    @classmethod
    def differ(cls, datas):
        # 将tabx中现有数据和datas比较
        diffs = {}
        _add = diffs["add"] = {}
        _del = diffs["del"] = {}
        _change = diffs["change"] = {}
        old = cls.datas_to_dict(datas)
        new = cls.datas_to_dict(cls.objects.to_list())
        for prefab, data in new.items():
            if prefab in old:
                stale = old.pop(prefab)
                for i, item in enumerate(data):
                    if item != stale[i]:
                        _change[prefab] = (stale, data)
                        break
            else:
                _add[prefab] = data
        if old:
            _del.update(old)
        return diffs

    @staticmethod
    def datas_to_dict(datas):
        res = {}
        for data in datas:
            # (fixme)更理想的情况是依赖主键，但现在只是第一项
            res[data[0]] = data
        return res


class ItemTable(Tabx):
    """对应ItemTable.tabx的类"""

    fields = {}
    _description = "饥荒联机版的代码、中、英、图片名对应表"

    id_ = StringField(primary_key=True)
    name_cn = StringField(blank=True, null=True)
    name_en = StringField()
    item_img1 = StringField()

    objects = Manager()

    def pre_save(self):
        self.name_cn = self.name_cn.replace('\\"', '"')
        self.name_en = self.name_en.replace('\\"', '"')


class DSTRecipes(Tabx):
    """对应DSTRecipes.tabx的类"""

    fields = {}
    _description = "饥荒联机版的合成配方列表"

    recipe_name = StringField(primary_key=True, zh="配方名称")
    ingredient1 = StringField(null=True, blank=True, zh="材料1")
    amount1 = NumberField(null=True, blank=True, zh="材料1数量")
    ingredient2 = StringField(null=True, blank=True, zh="材料2")
    amount2 = NumberField(null=True, blank=True, zh="材料2数量")
    ingredient3 = StringField(null=True, blank=True, zh="材料3")
    amount3 = NumberField(null=True, blank=True, zh="材料3数量")
    ingredient4 = StringField(null=True, blank=True, zh="材料4")
    amount4 = NumberField(null=True, blank=True, zh="材料4数量")
    ingredient5 = StringField(null=True, blank=True, zh="材料5")
    amount5 = NumberField(null=True, blank=True, zh="材料5数量")
    ingredient6 = StringField(null=True, blank=True, zh="材料6")
    amount6 = NumberField(null=True, blank=True, zh="材料6数量")
    product = StringField(blank=True, zh="产物")
    numtogive = NumberField(blank=True, zh="产物数量")
    override_numtogive_fn = BooleanField(blank=True, zh="产物数量函数")
    tech = StringField(zh="科技")
    hint_msg = StringField(null=True, blank=True, zh="提示信息")
    description = StringField(blank=True, null=True, zh="描述")
    nounlock = BooleanField(blank=True, zh="不可解锁")
    no_deconstruction = BooleanField(blank=True, zh="不可拆解")
    station_tag = StringField(blank=True, null=True, zh="制作站标签")
    builder_tag = StringField(blank=True, null=True, zh="制作者标签")
    builder_skill = StringField(blank=True, null=True, zh="制作者技能")
    desc = StringField(blank=True, null=True, zh="制作描述")

    objects = Manager()

    def pre_save(self):
        if self.product is None:
            self.product = self.recipe_name
        if self.numtogive is None:
            self.numtogive = 1


class DSTStrings(Tabx):
    """对应DST Strings {角色名}.tabx的类"""

    fields = {}
    _description = "饥荒联机版的角色台词列表"

    speech_character = StringField()
    speech_code = StringField()
    strings_code = StringField()
    strings_en = StringField()
    strings_cn = StringField(blank=True, null=True)

    objects = Manager()
