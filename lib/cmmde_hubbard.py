def azimuth(element):
    # Pemetaan bilangan kuantum azimut maksimum untuk masing-masing unsur    
    azimuth = {
    'Cl' : '3',
    'Al' : '3',
    'H': '1',
    'Cu': '3',
    'O' : '2',
    'N' : '2',
    'S' : '3',
    'P' : '3',
    'Br' : '3',
    'Ca' : '2',
    'F' : '2',
    'I' : '3',
    'K' : '2',
    'Na' : '2',
    'Zn' : '3',
    'Li' : '2',
    'B' : '2',
    'Au' : '3',
    'Rh' : '3',
    'Ni' : '3',
    'Co' : '3',
    'Ti' : '3',
    'C' : '2',
    'Si': '3'
    }
    return azimuth[element]

def hubbard(element):
    U = {'Br':'-0.0573','C':'-0.1492','Ca':'-0.0340','Cl':'-0.0697','F':'-0.1623','H':'-0.1857','I':'-0.0433','K':'-0.0339','Mg':'-0.02','N':'-0.1535','Na':'-0.0454','O':'-0.1575','P':'-0.14','S':'-0.11','Zn':'-0.03','Li': '-0.04548','B':'-0.145'}
    return U[element]
