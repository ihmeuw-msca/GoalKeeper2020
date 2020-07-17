"""
    composite_model
    ~~~~~~~~~~~~~~~
"""
from typing import List, Union, Dict, Tuple
import pandas as pd
import numpy as np
from copy import deepcopy

from mrtool import MRData, LinearCovModel
from .model import OverallModel, StudyModel


class StagewiseModel:

    def __init__(
        self,
        data: MRData,
        sub_models: List[Tuple[str, List[LinearCovModel]]],
    ):
        self.sub_models = sub_models
        self.num_sub_models = len(sub_models)
        self.datas = [data]
        self.fitted_models = []

    def _get_stage_data(self, data: MRData):
        pred = self.fitted_models[-1].predict(self.datas[-1])
        resi = self.datas[-1].obs - pred
        data_next = deepcopy(self.datas[-1])
        data_next.obs = resi

        self.datas.append(data_next)

    def fit_model(self):
        while len(self.sub_models) > 0:
            mtype, covmodels = self.sub_models.pop(0)
            if mtype == 'overall':
                self.fitted_models.append(OverallModel(self.datas[-1], covmodels))
            elif mtype == 'study':
                self.fitted_models.append(StudyModel(self.datas[-1], covmodels))
            else:
                raise ValueError(f'model type {mtype} is invalid.')
            self.fitted_models[-1].fit_model() 
            if len(self.sub_models) > 0:
                self._get_stage_data(self.datas[-1])     

    def predict(self, data: MRData = None, slope_quantile: Dict[str, float] = None):
        if data is None:
            data = self.datas[0]
        data._sort_by_data_id()
        pred = np.zeros(data.num_obs)
        for model in self.fitted_models:
            if model.__class__.__name__ == 'OverallModel':
                pred += model.predict(data)
            else:
                pred += model.predict(data, slope_quantile=slope_quantile)
        return pred

    def write_soln(self, i, path: str = None):
        return self.fitted_models[i].write_soln()
