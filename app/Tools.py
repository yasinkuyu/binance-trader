# -*- coding: UTF-8 -*-
# @yasinkuyu

class Tools():
     
    @staticmethod
    def e2f(flt):
        # Convert exponential form of float to decimal places
        was_neg = False
        if not ("e" in str(flt)):
            return flt
        if str(flt).startswith('-'):
            flt = flt[1:]
            was_neg = True 
        str_vals = str(flt).split('e')
        coef = float(str_vals[0])
        exp = int(str_vals[1])
        return_val = ''
        if int(exp) > 0:
            return_val += str(coef).replace('.', '')
            return_val += ''.join(['0' for _ in range(0, abs(exp - len(str(coef).split('.')[1])))])
        elif int(exp) < 0:
            return_val += '0.'
            return_val += ''.join(['0' for _ in range(0, abs(exp) - 1)])
            return_val += str(coef).replace('.', '')
        if was_neg:
            return_val='-'+return_val
        return return_val
    
