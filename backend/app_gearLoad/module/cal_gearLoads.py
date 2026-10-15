"""齿轮载荷计算：照搬网页版（tmb_web_v1 的 shanghai_yanfa7/utils.py）的 CalGearLoads、format_result、Excel

网页版还在用，两边要算得一样：这里的写法、命名、注释都原样保留，只去掉了 Django 相关的导入和发企业微信消息的函数。
Excel 类的属性名是单元格号（E12 压力角……E84），输入表按英文参数名取值。新模块不照着这里的写法写。
"""

import numpy as np
import pandas as pd


class CalGearLoads:
    def __init__(
        self,
            df_inputData: pd.DataFrame,
            df_selectedData: pd.DataFrame | None = None
    ):
        self.df_inputData = df_inputData.drop(columns=['editable'], errors='ignore')
        self.df_selectedData = df_selectedData
        self.stage_list = ["stageI", "stageII", "stageIII", "stageIIII"]

    def cal(self) -> dict:
        """
        说明
        ---
        - 计算齿轮载荷

        返回
        ---
        - 齿轮载荷结果
        """
        results_dict = {}

        for i in range(self.getNonEmptyColumns):
            if i != 0:
                self.df_inputData.loc["Torque T (kNm)", self.stage_list[i]] = results_dict[self.stage_list[i-1]]["input_data"][1]
                self.df_inputData.loc["Input speed n (RPM)", self.stage_list[i]] = results_dict[self.stage_list[i-1]]["input_data"][2]
            results = self._cal(self.stage_list[i])
            results_dict[self.stage_list[i]] = results
        return results_dict

    @property
    def getNonEmptyColumns(self) -> int:
        """
        说明
        ---
        - 计算整列不为空的列数

        返回
        ---
        - 整列不为空的列数
        """
        non_empty_columns = ((self.df_inputData != "") & (self.df_inputData.notna())).all().sum()
        return non_empty_columns

    def getExportData(self):
        """
        说明
        ---
        - 获取用于前端导出的齿轮载荷结果数据

        返回
        ---
        - 格式化的结果数据，供前端生成Excel
        """
        results = {}
        input_datas = []

        for i in range(self.getNonEmptyColumns):
            input_data_results = []
            gear_loads_results = []
            speed_of_components_results = []

            if i == 0:
                selected_data = self.df_selectedData.to_numpy()  # type: ignore
            else:
                selected_data = input_datas[i-1]

            for data_ in selected_data:
                if i == 0:
                    self.df_inputData.loc['Torque T (kNm)', self.stage_list[i]] = data_[1]
                    self.df_inputData.loc['Input speed n (RPM)', self.stage_list[i]] = data_[0]
                else:
                    self.df_inputData.loc['Torque T (kNm)', self.stage_list[i]] = data_[1]
                    self.df_inputData.loc['Input speed n (RPM)', self.stage_list[i]] = data_[2]
                result = self._cal(self.stage_list[i])
                input_data_results.append(result['input_data'])
                gear_loads_results.append(result['gear_loads'])
                speed_of_components_results.append(result['speed_of_components'])

            # 创建DataFrame以保持与pandas.to_excel()一致的格式
            df_gear_loads = pd.DataFrame(gear_loads_results)
            df_speed_of_components = pd.DataFrame(speed_of_components_results)
            df_res = pd.concat([df_gear_loads, df_speed_of_components], axis=1)
            df_res.columns = [
                '切向力 2Ftan(KN)', '行星轮-太阳轮-切向力(KN)', '行星轮-太阳轮-径向力(KN)',
                '行星轮-太阳轮-轴向力(KN)', '行星轮-齿圈-切向力(KN)', '行星轮-齿圈-径向力(KN)',
                '行星轮-齿圈-轴向力(KN)', '扭矩T(KNm)', '轴向力太阳轮(KN)',
                '太阳轮转速(RPM)', '行星轮转速(RPM)', '齿圈转速(RPM)'
            ]

            # 转换为前端需要的格式，包含索引列
            headers_with_index = [''] + df_res.columns.tolist()  # 第一列是索引列的表头（空字符串）
            data_with_index = []

            for idx, row in df_res.iterrows():
                row_data = [str(idx)] + row.tolist()  # 第一列是索引值
                data_with_index.append(row_data)

            results[self.stage_list[i]] = {
                'headers': headers_with_index,
                'data': data_with_index
            }
            input_datas.append(input_data_results)

        return results

    def _cal(self, stage_level: str):
        isPlanets = self.df_inputData.loc["Gear stage arrangement", stage_level] == "Planetary"
        excel = Excel(
            self.df_inputData,
            isPlanets=isPlanets, # type: ignore
            stage_level=stage_level,
        )
        # TITLE 齿轮载荷结果存储 stageI
        results = {}
        # Input data
        input_data_results = []
        input_data_results.append(format_result(excel.E22))
        input_data_results.append(format_result(excel.E41))
        if isPlanets:
            _ = format_result(excel.E46)
        else:
            _ = format_result(excel.E47)
        input_data_results.append(_)
        results["input_data"] = input_data_results
        # Gear loads
        gear_loads_results = []
        gear_loads_results.append(format_result(excel.E31))
        gear_loads_results.append(format_result(excel.E33))
        gear_loads_results.append(format_result(excel.E34))
        gear_loads_results.append(format_result(excel.E35))
        gear_loads_results.append(format_result(excel.E37))
        gear_loads_results.append(format_result(excel.E38))
        gear_loads_results.append(format_result(excel.E39))
        gear_loads_results.append(format_result(excel.E41))
        gear_loads_results.append(format_result(excel.E42))
        results["gear_loads"] = gear_loads_results
        # Speed of components
        speed_of_components_results = []
        speed_of_components_results.append(format_result(excel.E46))
        speed_of_components_results.append(format_result(excel.E47))
        speed_of_components_results.append(format_result(excel.E48))
        results["speed_of_components"] = speed_of_components_results
        # Equivalent diameter
        equivalent_diameter_results = []
        equivalent_diameter_results.append(format_result(excel.E52))
        equivalent_diameter_results.append(format_result(excel.E53))
        equivalent_diameter_results.append(format_result(excel.E54))
        results["equivalent_diameter"] = equivalent_diameter_results
        # 返回所有结果
        return results


def format_result(value, precision=3):
    """
    格式化结果：
    - 如果是有限数字，保留指定的小数位数
    - 如果是无穷大，返回 "Infinity" 或 "-Infinity"
    - 如果是 NaN，返回 ""
    - 如果是其他类型，保持不变
    """
    if isinstance(value, (int, float)):
        if np.isinf(value):
            return "Infinity" if value > 0 else "-Infinity"
        elif np.isnan(value):
            return ""
        else:
            return round(value, precision)
    else:
        return value


class Excel:
    """
    常数类
    """

    def __init__(self, df: pd.DataFrame, isPlanets: bool, stage_level: str) -> None:
        self.df = df.apply(pd.to_numeric, errors='coerce')
        self.isPlanets = isPlanets
        self.stage_level = stage_level

    @property
    def E12(self):
        return self.df.loc["Nominal pressure angle αn (°)", self.stage_level]

    @property
    def E13(self):
        return self.df.loc["Helix angle β (°)", self.stage_level]

    @property
    def E14(self):
        return self.df.loc["Helix angle LH of RH - sun wheel or pinion", self.stage_level]

    @property
    def E15(self):
        return self.df.loc["Module in the normal section mn (mm)", self.stage_level]

    @property
    def E16(self):
        return self.df.loc["Number of teeth ring wheel zR / wheel z1", self.stage_level]

    @property
    def E17(self):
        return self.df.loc["Number of teeth planet zpl / pinion z2", self.stage_level]

    @property
    def E18(self):
        return self.df.loc["Number of teeth sun zsun", self.stage_level]

    @property
    def E19(self):
        return self.df.loc["Centre distance a (mm)", self.stage_level]

    @property
    def E20(self):
        return self.df.loc["Number of planets", self.stage_level]

    @property
    def E22(self):
        return self.df.loc["Power P (kW)", self.stage_level]

    @property
    def E23(self):
        return self.df.loc["Torque T (kNm)", self.stage_level]

    @property
    def E24(self):
        return self.df.loc["Input speed n (RPM)", self.stage_level]

    @property
    def E26(self):
        return self.df.loc["Root diameter df (mm)", self.stage_level]

    @property
    def E27(self):
        return self.df.loc["Tip diameter da (mm)", self.stage_level]

    @property
    def E28(self):
        return self.df.loc["Load factor KY", self.stage_level]

    @property
    def E31(self):
        if self.isPlanets:
            return 1000*(self.E23/self.E20)*(1/self.E19)*self.E28  # type: ignore
        else:
            return np.nan

    @property
    def E33(self):
        if self.isPlanets:
            return self.E37*(self.E65/self.E66)  # type: ignore
        else:
            return 2000*self.E23/self.E64  # type: ignore

    @property
    def E34(self):
        return self.E33*self.E78  # type: ignore

    @property
    def E35(self):
        return self.E33*self.E80  # type: ignore

    @property
    def E37(self):
        if self.isPlanets:
            return (self.E31*self.E66)/(self.E65+self.E66)  # type: ignore
        else:
            return np.nan

    @property
    def E38(self):
        if self.isPlanets:
            return self.E37*self.E82  # type: ignore
        else:
            return np.nan

    @property
    def E39(self):
        if self.isPlanets:
            return self.E37*self.E84  # type: ignore
        else:
            return np.nan

    @property
    def E41(self):
        if self.isPlanets:
            return self.E23/((1+(np.abs(self.E16)/self.E18)))  # type: ignore
        else:
            return self.E23*self.E17/np.abs(self.E16)  # type: ignore

    @property
    def E42(self):
        if self.isPlanets:
            return self.E35*self.E20/self.E28  # type: ignore
        else:
            return np.nan

    @property
    def E46(self):
        if self.isPlanets:
            return self.E24*(1+(self.E16/self.E18))  # type: ignore
        else:
            return self.E24

    @property
    def E47(self):
        if self.isPlanets:
            return -self.E24*(self.E16/self.E17)  # type: ignore
        else:
            return self.E24*self.E16/self.E17  # type: ignore

    @property
    def E48(self):
        if self.isPlanets:
            return 0
        else:
            return np.nan

    @property
    def E52(self):
        if self.isPlanets:
            return self.E66/2  # type: ignore
        else:
            if self.E26 == 0 and self.E27 == 0:
                return self.E65
            else:
                return 0.5*(self.E26+self.E27)  # type: ignore

    @property
    def E53(self):
        if self.isPlanets:
            return self.E65/2  # type: ignore
        else:
            return np.nan

    @property
    def E54(self):
        if self.isPlanets:
            if self.E26 == 0 and self.E27 == 0:
                return np.nan
            else:
                return 0.5*(self.E26+self.E27)  # type: ignore
        else:
            return np.nan

    @property
    def E60(self):
        if self.isPlanets:
            return -self.E15*self.E16  # type: ignore
        else:
            return self.E15*self.E16  # type: ignore

    @property
    def E61(self):
        return self.E15*self.E17  # type: ignore

    @property
    def E62(self):
        if self.isPlanets:
            return self.E15*self.E18  # type: ignore
        else:
            return np.nan

    @property
    def E64(self):
        if self.isPlanets:
            return -(2*self.E19)/(1+(-self.E17/self.E16))  # type: ignore
        else:
            return (2*self.E19)/(1+(self.E17/self.E16))  # type: ignore

    @property
    def E65(self):
        if self.isPlanets:
            return -(2*self.E19)/((-self.E16/self.E17)+1)  # type: ignore
        else:
            return (2*self.E19)/((self.E16/self.E17)+1)  # type: ignore

    @property
    def E66(self):
        if self.isPlanets:
            return 2*self.E19/((self.E18/self.E17)+1)  # type: ignore
        else:
            return np.nan

    @property
    def E69(self):
        return np.arctan(np.tan(np.pi*self.E12/180)/np.cos(np.pi*self.E13/180))  # type: ignore

    @property
    def E71(self):
        return self.E60*np.cos(self.E69)/np.cos(self.E13*np.pi/180)  # type: ignore

    @property
    def E72(self):
        return self.E61 * np.cos(self.E69) / np.cos(self.E13 * np.pi / 180)  # type: ignore

    @property
    def E73(self):
        if self.isPlanets:
            return self.E62*np.cos(self.E69)/np.cos(self.E13*np.pi/180)  # type: ignore
        else:
            return np.nan

    @property
    def E75(self):
        return np.arccos((self.E71+self.E72)/(2*self.E19))  # type: ignore

    @property
    def E76(self):
        if self.isPlanets:
            return np.arccos((self.E72+self.E73)/(2*self.E19))  # type: ignore
        else:
            return np.nan

    @property
    def E78(self):
        if self.isPlanets:
            return np.tan(self.E76)  # type: ignore
        else:
            return np.tan(self.E75)  # type: ignore

    @property
    def E80(self):
        if self.isPlanets:
            return np.tan(np.pi*self.E13/180)*np.cos(self.E69)/np.cos(self.E76)  # type: ignore
        else:
            return np.tan(np.pi*self.E13/180)*np.cos(self.E69)/np.cos(self.E75)  # type: ignore

    @property
    def E82(self):
        if self.isPlanets:
            return -np.tan(self.E75)  # type: ignore
        else:
            return np.nan

    @property
    def E84(self):
        if self.isPlanets:
            return -np.tan(np.pi*self.E13/180)*np.cos(self.E69)/np.cos(self.E75)  # type: ignore
        else:
            return np.nan
