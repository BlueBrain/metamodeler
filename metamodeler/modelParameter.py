# -*- coding: utf-8 -*-
"""
Created on Mon Oct  3 12:33:55 2016

@author: oreilly
"""


import quantities as pq
import numpy as np
from nat.modelingParameter import ParameterInstance

class AbstractParameterInstance:
    # This class represent a parameter instance. It can be used to
    # represent 1) a parameter that is specified in a
    # modeling file (e.g. .mm_py, .mm_hoc, .mm_mod) with the #|...|#
    # formalism or 2) a parameter specified by a given annotation.
    # The objects encode the type of parameter, its numerical value,
      # the units in which it is specified, and the annotation and publication
    # ID it refers to.

    def __init__(self):
        self.__unit         = None
        self.__value        = None

    def setValue(self, value, unit):
        # A value must always be set along with its unit. Else, it is meaningless.
        self.__unit     = unit
        self.__value    = value

    def convertUnit(self, unit):
        pass


    @property
    def unit(self):
        # Make unit validation
        return self.__unit

    @property
    def value(self):
        return self.__value

    def isComplete(self):
        # No need to check unit because value-units are always
        # set in pairs.
        if self.value is None:
            return False
        if self.unit is None:
            return False

        return True


class Transformation:

    def __init__(self):
        self.transformationCode = ""    
    
    def toJSON(self):
        return {"transformationCode": self.transformationCode}
        
    def apply(self, referenceInstances):
        if len(referenceInstances) == 0 :
            return None, None
        
        if self.transformationCode == "":
            print([ref.centralTendancy() for ref in referenceInstances])
            print([type(ref.centralTendancy()) for ref in referenceInstances])
            quantities = [pq.Quantity(np.mean(ref.centralTendancy()), ref.unit) for ref in referenceInstances]

            # Rescale to a common unit and average
            unit = str(quantities[0].dimensionality)

            # The following code does not work because of a probable bug
            # in the Quantity library: https://github.com/python-quantities/python-quantities/issues/123
            #mean = np.mean([quant.rescale(unit).base  for quant in quantities])
            # Thus we replace by the more verbose version...
            mean = np.mean([quant.rescale(unit).base if unit != str(quant.dimensionality) else quant.base for quant in quantities])
            
            return mean, unit 
        else:
            raise NotImplemented            
            

class ModelParameterInstance (AbstractParameterInstance):

    def __init__(self, paramID, referenceInstances=None, transformation=None):
        super(ModelParameterInstance, self).__init__()
        self.paramID              = paramID
        self.__referenceInstances = []   
        self.__transformation     = Transformation()       
        
        if isinstance(referenceInstances, ParameterInstance):
            self.referenceInstances = [referenceInstances]
        elif isinstance(referenceInstances, list):
            self.referenceInstances = referenceInstances
        elif referenceInstances is None:
            self.referenceInstances = []
        else:
            raise TypeError()
            
        if not transformation is None:
            self.transformation     = transformation
            

        self.__unit         = None
        self.__value        = None

    
    @property
    def ids(self):
        return [ref.id for ref in self.referenceInstances] 
    
    @property
    def referenceInstances(self):
        return self.__referenceInstances
        
    @referenceInstances.setter
    def referenceInstances(self, referenceInstances):
        if not isinstance(referenceInstances, list):
            raise TypeError()
        self.__referenceInstances = referenceInstances
        self.setValue(*self.transformation.apply(self.referenceInstances))
        
    @property
    def transformation(self):
        return self.__transformation
        
    @transformation.setter
    def transformation(self, transformation):
        if not isinstance(transformation, Transformation):
            raise TypeError("The argument 'transformation' must be of type 'Transformation'. Received type '" + str(transformation) + "'")
        self.__transformation = transformation
        self.value, self.unit = self.__transformation.apply(self.referenceInstances)
        
        
        

    def toJSON(self):
        return {"unit": self.unit, 
                "value": self.value,
                "paramID": self.paramID,
                "referenceInstances": [ref.toJSON() for ref in self.referenceInstances],
                "transformation": self.transformation.toJSON() if not self.transformation is None else None}



class CustomParameterInstance (AbstractParameterInstance):

    def __init__(self, name, justification = None):
        super(CustomParameterInstance, self).__init__()
        self.name            = name
        self.justification   = justification

    def isComplete(self):
        # No need to check unit because value-units are always
        # set in pairs.
        if self.value is None:
            return False

        if self.justification is None:
            return False

        return True


    def toJSON(self):
        return {"unit": self.unit, 
                "value": self.value,
                "name": self.name,
                "justification": self.justification}




