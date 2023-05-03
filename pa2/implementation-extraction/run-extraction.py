import sys
import regex
import xpath
import TheBestExtractionAlgorithmEverTM

rtv_a = open("../input-extraction/rtvslo.si/Audi A6 50 TDI quattro_ nemir v premijskem razredu - RTVSLO.si.html", encoding="utf-8").read()
rtv_b = open("../input-extraction/rtvslo.si/Volvo XC 40 D4 AWD momentum_ suvereno med najboljše v razredu - RTVSLO.si.html", encoding="utf-8").read()

jewelry_a = open("../input-extraction/overstock.com/jewelry01.html").read()
jewelry_b = open("../input-extraction/overstock.com/jewelry02.html").read()

mimovrste_a = open("../input-extraction/mimovrste.si/mimovrste_1.html", encoding="utf-8").read()
mimovrste_b = open("../input-extraction/mimovrste.si/mimovrste_2.html", encoding="utf-8").read()


if sys.argv[1] == "A":
    print('Overstock:')
    regex.getOverstock(jewelry_a)
    regex.getOverstock(jewelry_b)
    
    print('RTV:')
    regex.getRTV(rtv_a)
    regex.getRTV(rtv_b)

    print('Mimovrste:')
    regex.getMimovrste(mimovrste_a)
    regex.getMimovrste(mimovrste_b)


elif sys.argv[1] == "B":
    print('Overstock')
    xpath.getOverstock(jewelry_a)
    xpath.getOverstock(jewelry_b)

    print('RTV')
    xpath.getRTV(rtv_a)
    xpath.getRTV(rtv_b)

    print('Mimovrste')
    xpath.getMimovrste(mimovrste_a)
    xpath.getMimovrste(mimovrste_b)

elif sys.argv[1] == "C":
    print('road runner')

    #print('Overstock')
    #TheBestExtractionAlgorithmEverTM.getOverstock(jewelry_a, jewelry_b)

    #print('RTV')
    #TheBestExtractionAlgorithmEverTM.getRTV(rtv_a, rtv_b)

    #print('Mimovrste')
    #TheBestExtractionAlgorithmEverTM.getMimovrste(mimovrste_a, mimovrste_b)
else:
    print("Error: wrong key. Please use 'A', 'B', or 'C' as the input.")