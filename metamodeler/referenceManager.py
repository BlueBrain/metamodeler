# -*- coding: utf-8 -*-
"""
Created on Tue Oct 25 18:16:16 2016

@author: oreilly
"""


from nat.id import getInfoFromID
import pickle

class ReferenceManager:
    
        
    def getInfoFromID(self, pubId, alwaysFetch=False):
        """
         Accessing web-based ontology service is too long, so we cache the 
         information in a pickle file and query the services only if the info
         has not already been cached. 
        """
    
        if not alwaysFetch:
            try:
                with open("pubInfo.bin", "rb") as infoFile:
                    infoPub = pickle.load(infoFile)
                    
                if pubId in infoPub:
                    return infoPub[pubId]                
            except:
                infoPub = {}
        
        NB_TRY_MAX = 3
        for tryNo in range(NB_TRY_MAX):
            try:
                infoPub[pubId] = getInfoFromID(pubId)
                break
            except ConnectionResetError:
                if tryNo == NB_TRY_MAX-1:
                    return None
    
        try:
            with open("pubInfo.bin", "wb") as infoFile:
                pickle.dump(infoPub, infoFile)
        except:
            pass        
    
        return infoPub[pubId]   