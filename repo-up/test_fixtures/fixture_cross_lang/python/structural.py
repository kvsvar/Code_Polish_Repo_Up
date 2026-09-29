# Python cross-language fixture — structural.py
# Deep inheritance, high WMC, no README (structural issues at repo level are
# checked separately; this file exercises metric-based structural rules).


class A:
    pass


class B(A):
    pass


class C(B):
    def m1(self): pass
    def m2(self): pass
    def m3(self): pass
    def m4(self): pass
    def m5(self): pass
    def m6(self): pass
    def m7(self): pass
    def m8(self): pass
    def m9(self): pass
    def m10(self): pass
    def m11(self): pass
    def m12(self): pass
    def m13(self): pass
    def m14(self): pass
    def m15(self): pass
    def m16(self): pass  # > 15 methods => METRIC-HIGH-WMC
    # DIT: C -> B -> A => DIT = 3 => METRIC-DEEP-DIT
