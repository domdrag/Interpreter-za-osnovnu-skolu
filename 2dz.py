import fractions
from pj import *
import math

BKSL, N1, N2, NOVIRED, KOMENTAR = '\\', "'", '"', '\n', '#'

def makni(it):
    """Miče obrnute kose crte (backslashes) iz iteratora."""
    for znak in it:
        if znak == BKSL:
            sljedeći = next(it)
            if sljedeći == 'n': yield NOVIRED
            else: yield sljedeći
        else: yield znak

class INF(enum.Enum):
    AKO, INAČE, FOR = 'ako', 'inače', 'for'
    JE, NIJE, ILI = 'je', 'nije', 'ili'
    OOTV, OZATV, VOTV, VZATV = '(){}'
    ZAREZ, JEDNAKO, PLUS, MINUS, PUTA, KROZ = ',=+-*/'
    MANJE, VEĆE  = '<>'
    MANJE_ILI_JEDNAKO = '<='
    VEĆE_ILI_JEDNAKO = '>='
    RAZLIČITO = '!='
    PLUSP, JJEDNAKO = '++', '=='
    ISPIS = 'ispis'
    PRETVORI = 'pretvori'
    UPIS = 'upis'
    TOČKAZ = ';'
    
    class BROJ(Token):
        """Aritmetička konstanta (prirodni broj)."""
        def vrijednost(self, mem): return int(self.sadržaj)
        
    class IME(Token):
        """Ime za broj ili string """
        def vrijednost(self, mem): return pogledaj(mem, self)
        
    class STRING(Token):
        def vrijednost(self,mem):
            """Vrati vrijednost unutar apostrofa"""
            s = self.sadržaj[1:-1]
            if self.sadržaj.startswith(N2): return ''.join(makni(iter(s)))
            else: return s
            
    class KOMENTAR(Token):
        def vrijednost(self):
            """Vrati vrijednost unutar #...#"""
            s = self.sadržaj[1:-1]
            return s


def INF_lex(program):
    lex = Tokenizer(program)
    for znak in iter(lex.čitaj, ''):
        if znak.isspace(): lex.zanemari()
        elif znak.isalpha():
            lex.zvijezda(str.isalpha)
            yield lex.literal(INF.IME)
        elif znak == N1:
            lex.pročitaj_do(N1)
            yield lex.token(INF.STRING)
        elif znak == N2:
            while True:
                z = lex.čitaj()
                if not z: raise lex.greška('Nezavršeni string!')
                elif z == BKSL: lex.čitaj()
                elif z == N2:
                    yield lex.token(INF.STRING)
                    break
        elif znak == KOMENTAR:
            lex.pročitaj_do(KOMENTAR)
            yield lex.token(INF.KOMENTAR)
        elif znak.isdigit():
            lex.zvijezda(str.isdigit)
            yield lex.token(INF.BROJ)
        elif znak == '!':
            lex.pročitaj('=')
            yield lex.token(INF.RAZLIČITO)
        elif znak == '<':
            if lex.slijedi('='): yield lex.token(INF.MANJE_ILI_JEDNAKO)
            else: yield lex.token(INF.MANJE)
        elif znak == '>':
            if lex.slijedi('='): yield lex.token(INF.VEĆE_ILI_JEDNAKO)
            else: yield lex.token(INF.VEĆE)
        elif znak == '+':
            if lex.slijedi( '+' ):
                lex.čitaj()
                yield lex.token( INF.PLUSP )
            else: yield lex.token( INF.PLUS )

        elif znak == '=':
            if lex.slijedi('='): yield lex.token(INF.JJEDNAKO)
            else: yield lex.token(INF.JEDNAKO)
        else: yield lex.literal(INF)

###BESKONTEKSTNA GRAMATIKA
# program -> '' | naredba | naredba program
# naredba -> pridruži | granaj | petlja | ispis | upis | komentar
# pridruži -> IME JEDNAKO izraz TOČKAZ
# granaj -> AKO OOTV IZRAZ operator IZRAZ OZATV VOTV program VZATV  |
#           AKO OOTV IZRAZ operator IZRAZ OZATV VOTV program VZATV INAČE VOTV program VZATV
# petlja -> FOR OOTV IME JEDNAKO IZRAZ TOČKAZ IZRAZ OZATV VOTV program VZATV
# ispis -> ISPIS izraz TOČKAZ
# upis -> UPIS IME TOČKAZ
# izraz -> izraz PLUS član | izraz MINUS član | član
# član -> član PUTA faktor | član KROZ faktor | član OOTV izraz OZATV | faktor
# faktor -> pretvori | IME | konst | OOTV izraz OZATV
# operator -> JEDNAKO | PLUS | MINUS | PUTA | KROZ | MANJE | VEĆE | MANJE_ILI_JEDNAKO | VEĆE_ILI_JEDNAKO | RAZLIČITO
# pretvori -> PRETVORI OOTV IME OZATV

class INF_parser(Parser):
    def program(self):
        naredbe = []
        while not self >> E.KRAJ: naredbe.append(self.naredba())
        return Program(naredbe)
    def naredba(self):
        if self >= INF.IME:
            return self.pridruži()
        elif self >= INF.AKO:
            return self.granaj()
        elif self >= INF.FOR:
            return self.petlja()
        elif self >= INF.ISPIS:
            return self.ispis()
        elif self >= INF.UPIS:
            return self.upis()
        elif self >> INF.KOMENTAR:
            return self.komentar()
        else: raise self.greška()

    def pridruži(self):
        ime = self.ime()
        self.pročitaj(INF.JEDNAKO)
        value = self.izraz()
        self.pročitaj(INF.TOČKAZ)
        return Pridruzi(ime,value)
    
    def granaj(self):
        self.pročitaj(INF.AKO)
        self.pročitaj(INF.OOTV)
        izraz = self.izraz()
        operator = self.operator()
        izraz2 = self.izraz()
        naredbe_if = []
        naredbe_else = []
        ispunjen = Uvjet(izraz, izraz2, operator)
        self.pročitaj(INF.OZATV)
        self.pročitaj(INF.VOTV)
        while not self >> INF.VZATV : naredbe_if.append( self.naredba() )
        if self >= INF.INAČE:
            self.pročitaj(INF.INAČE)
            self.pročitaj(INF.VOTV)
            while not self >> INF.VZATV : naredbe_else.append( self.naredba() )
        return Granaj(ispunjen, naredbe_if , naredbe_else)
    
    def petlja(self):
        self.pročitaj(INF.FOR)
        self.pročitaj(INF.OOTV)
        ime= self.ime()
        self.pročitaj(INF.JEDNAKO)
        broj1 = self.izraz()
        self.pročitaj(INF.TOČKAZ)
        broj2 = self.izraz()
        self.pročitaj(INF.OZATV)
        self.pročitaj(INF.VOTV)
        naredbe = []
        while not self >> INF.VZATV : naredbe.append( self.naredba() )
        return Petlja( ime, broj1 , broj2, naredbe )

    def ispis(self):
        self.pročitaj(INF.ISPIS)
        izraz = self.izraz()
        self.pročitaj(INF.TOČKAZ)
        return Ispis(izraz)

    def upis(self):
        self.pročitaj(INF.UPIS)
        self.pročitaj(INF.OOTV)
        ime = self.ime()
        self.pročitaj(INF.OZATV)
        self.pročitaj(INF.TOČKAZ)
        return Upis(ime)

    def izraz(self):
        trenutni = self.član()
        while True:
            if self >> INF.PLUS:
                trenutni = Zbroj(trenutni, self.član())
            elif self >> INF.MINUS:
                član = self.član()
                trenutni = Zbroj(trenutni, Suprotan(član))
            else: break
        return trenutni

    def član(self):
        if self >> INF.MINUS:
            return Suprotan(self.član())
        trenutni = self.faktor()
        while True:
            if self >> INF.PUTA or self >= INF.OOTV:
                trenutni = Umnožak(trenutni, self.faktor())
            elif self >> INF.KROZ:
                faktor = self.faktor()
                trenutni = Umnožak( trenutni, Recipročan(faktor))
            else: break
        return trenutni
            
    def faktor(self):
        if self >= INF.BROJ or self >= INF.STRING: return self.konst()
        elif self >= INF.IME: return self.ime()
        elif self >> INF.OOTV:
            izraz = self.izraz()
            self.pročitaj(INF.OZATV)
            return izraz
        else:
            self.pročitaj(INF.PRETVORI)
            self.pročitaj(INF.OOTV)
            ime = self.ime()
            self.pročitaj(INF.OZATV)
            return Pretvori(ime)

    def ime(self):
        if self >> INF.IME:
            return self.zadnji
        else:
            raise self.greška()

    def konst(self):
        if self >> INF.BROJ:
            return self.zadnji
        elif self >> INF.STRING:
            return self.zadnji
        else:
            raise self.greška()
        
    def operator(self):
        if self >> INF.JEDNAKO or self >> INF.PLUS or self >> INF.MINUS or self >> INF.PUTA:
            return self.zadnji
        elif self >> INF.KROZ or self >> INF.MANJE or self >> INF.VEĆE or self >> INF.MANJE_ILI_JEDNAKO:
            return self.zadnji
        elif self >> INF.VEĆE_ILI_JEDNAKO or self >> INF.RAZLIČITO or self >> INF.JJEDNAKO:
            return self.zadnji
        else:
            raise self.greška()

    def komentar(self):
        return Komentar(self.zadnji)

    start = program

###Apstraktna sintaksna stabla:
# Program: naredbe:list
# Pridruzi: ime:IME vrijednost:izraz
# Granaj: ispunjen:bool, naredbe_if:list, naredbe_else:list
# Petlja: ime:IME, početak:izraz, kraj:izraz, naredbe:list
# Ispis: izraz:izraz
# Upis: ime:IME
# Zbroj: lijevo:clan, desno:clan
# Suprotan: od:izraz
# Reciprocan: od:izraz
# Umnozak: lijevo:faktor, desno:faktor
# Komentar: komentar:komentar
# Pretvori: ime:IME
# Uvjet: izraz1:izraz izraz2:izraz operator:operator

class Program(AST('naredbe')):
    def izvrši(self):
        mem = {}
        for naredba in self.naredbe: naredba.izvrši(mem)

class Pridruzi(AST('ime value')):
    def izvrši(self, mem):
        x = self.ime
        mem[x.sadržaj] = self.value.vrijednost(mem)

class Granaj(AST('ispunjen naredbe_if naredbe_else')):
    def izvrši(self, mem):
        if (self.ispunjen.vrijednost(mem) == 1):
            for naredba in self.naredbe_if: naredba.izvrši(mem)
        else:
            for naredba in self.naredbe_else: naredba.izvrši(mem)

class Petlja(AST('var broj kraj for_naredbe')):
    def izvrši(self, mem):
        v = self.var
        mem[v.sadržaj] = self.broj.vrijednost(mem)
        if (v.vrijednost(mem) <= self.kraj.vrijednost(mem)):
            while (v.vrijednost(mem) < self.kraj.vrijednost(mem)):
                for naredba in self.for_naredbe :
                    naredba.izvrši(mem)
                mem[v.sadržaj] += 1
        else:
            while (v.vrijednost(mem) > self.kraj.vrijednost(mem)):
                for naredba in self.for_naredbe :
                    naredba.izvrši(mem)
                mem[v.sadržaj] -= 1

class Ispis(AST('izraz')):
    def izvrši(self, mem):
        print(self.izraz.vrijednost(mem), end='\n')

class Upis(AST('ime')):
    def izvrši(self, mem):
        x = self.ime.sadržaj
        u = input('')
        if u.isdigit():
            mem[x] = int(u)
        else:
            mem[x] = u

class Zbroj(AST('lijevo desno')):
    def vrijednost(self, mem):
        l, d = self.lijevo.vrijednost(mem), self.desno.vrijednost(mem)
        if type(l) != type(d):
            raise NotImplementedError("Neće moći ove noći")
        else:
            return l + d

class Suprotan(AST('od')):
    def vrijednost(self, mem):
        if type(self.od.vrijednost(mem)) is int:
            return -self.od.vrijednost(mem)
        else:
            raise NotImplementedError('Nesto si mi krivo dao, nesto sto ne znam')

class Recipročan(AST('od')):
    def vrijednost(self, mem):
        if type(self.od.vrijednost(mem)) is int:
            if self.od.vrijednost(mem) != 0:
                return 1/self.od.vrijednost(mem)
            else:
                raise ArithmeticError('Pokusavas doci kud ne smijes')
        else:
            raise NotImplementedError('Sto si mi to dao')

class Umnožak(AST('lijevo desno')):
    def vrijednost(self, mem):
        l, d = self.lijevo.vrijednost(mem), self.desno.vrijednost(mem)
        if type(l) is int:
            if type(l) is int or float:
                return math.floor(l * d)
        else:
            raise NotImplementedError('Zasto mi to opet radis')

class Komentar(AST('komentar')):
    def izvrši(self, mem):
        pass

class Pretvori(AST('ime')):
    def vrijednost(self, mem):
        value = self.ime.vrijednost(mem)
        if type(value) == int:
            return str(value)
        if type(value) == str:
            if value.isdigit():
                return int(value)
            else:
                raise NotImplementedError('Opet radis nesto sto ne smijes, zlocko')

class Uvjet(AST('lijevo desno operator')):
    def vrijednost(self,mem):
        l = self.lijevo.vrijednost(mem)
        d = self.desno.vrijednost(mem)
        op = self.operator.sadržaj
        if type( l ) != type( d ):
            print (type(l))
            print (type(d))
            raise NotImplementedError("Kud si pošo, sine maleni?")
        elif op == '<':
            if l < d: return 1
            else: return 0
        elif op == '<=':
            if l <= d: return 1
            else: return 0
        elif op == '>':
            if l > d: return 1
            else: return 0
        elif op == '>=':
            if l >= d: return 1
            else: return 0
        elif op == '==':
            if l == d: return 1
            else: return 0
        elif op == '!=':
            if l != d: return 1
            else: return 0
            

if __name__ == '__main__':
    primjer1 = '''\
                ispis("Upisi string: ");
                upis(s); 
                ispis(s);
                '''
    tokeni = list(INF_lex(primjer1))
    print(*tokeni)
    pars = INF_parser.parsiraj(tokeni)
    pars.izvrši()
    
    primjer2 = '''\
                ispis("Upisi dva broja: ");
                upis(a); 
                upis(b); 
                c=a+b; 
                ispis(c);
                '''
    tokeni = list(INF_lex(primjer2))
    print(*tokeni)
    pars = INF_parser.parsiraj(tokeni)
    pars.izvrši()

    primjer3 = '''\
                ispis("Upisi dva broja: ");
                upis(a);
                upis(b);
                ako (a >= b){ #Ukoliko je prvi upisani veci od drugoga ispisi ga (Ako su jednaki svejedno je kojeg ispisujemo)#
                    ispis(a);
                }
                inače{ #U suprotnom ispisi drugoga#
                    ispis(b);
                }
                '''
    tokeni = list(INF_lex(primjer3))
    print(*tokeni)
    pars = INF_parser.parsiraj(tokeni)
    pars.izvrši()

    primjer4 = '''\
                ispis("Upisi n:");
                upis(n);
                ispis("Upisi visine ucenika:");
                upis(v);
                max = v;
                min = v;
                for (i=0;n-1){
                    upis(v);
                    ako (v > max){ #Ako je zadnja upisana visina veca od maksimalne dosad upisane, onda je ta visina maksimalna.#
                        max = v; 
                    }
                    ako (v < min){ #Analogno prijasnjem#
                        min = v;
                    }
                }
                ispis("Najvisi ucenik");
                ispis(max);
                ispis("Najnizi ucenik");
                ispis(min);     
                '''
    tokeni = list(INF_lex(primjer4))
    print(*tokeni)
    pars = INF_parser.parsiraj(tokeni)
    pars.izvrši()
    
    primjer5 = '''\
                    ispis("Upisi broj: ");
                    upis(n);
                    str = "";
                    for(i=2;n){
                        #Pretpostavljamo da je broj prost dok se ne pokaže suprotno#
                        prost=1;
                        for(j=2;i){
                            d=i/j;
                            #Ako je broj djeljiv sa nekim brojem osim s njim ili 1 => nije prost#
                            ako(d*j == i){
                                prost=0;
                            }
                        }
                        #Ako je prost konkateniramo ga u string#
                        ako(prost == 1){
                            str = str + pretvori(i) + " " ;
                        }
                    }
                    ispis(str);
                '''
    tokeni = list(INF_lex(primjer5))
    print(*tokeni)
    pars = INF_parser.parsiraj(tokeni)
    pars.izvrši()