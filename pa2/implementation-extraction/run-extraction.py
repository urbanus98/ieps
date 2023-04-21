import sys
import regex
import xpath

rtv_a = open("../input-extraction/rtvslo.si/Audi A6 50 TDI quattro_ nemir v premijskem razredu - RTVSLO.si.html", encoding="utf-8").read()
rtv_b = open("../input-extraction/rtvslo.si/Volvo XC 40 D4 AWD momentum_ suvereno med najboljše v razredu - RTVSLO.si.html", encoding="utf-8").read()

jewelry_a = open("../input-extraction/overstock.com/jewelry01.html").read()
jewelry_b = open("../input-extraction/overstock.com/jewelry02.html").read()


if sys.argv[1] == "A":
    print('Overstock:')
    regex.getOverstock(jewelry_a)
    regex.getOverstock(jewelry_b)
    
    print('RTV:')
    regex.getRTV(rtv_a)
    regex.getRTV(rtv_b)


elif sys.argv[1] == "B":
    print('Overstock')
    xpath.getOverstock(jewelry_a)
    xpath.getOverstock(jewelry_b)

    print('RTV')
    xpath.getRTV(rtv_a)
    xpath.getRTV(rtv_b)

elif sys.argv[1] == "C":
    print('road runner')
