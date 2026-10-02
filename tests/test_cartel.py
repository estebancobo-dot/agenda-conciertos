from scraper.cartel import cartel_de_titulo, clave_festival, es_festival, nombre_festival


def test_es_festival():
    assert es_festival("Madcore Fest") and es_festival("METAL on METAL: tribute Festival")
    assert es_festival("SANTUARIO Festival en Madrid - 2026 - SE APLAZA a 2027")
    assert not es_festival("MININO BRAVO (Festival JazzMadrid)")  # toca en un festival: es su ciclo
    assert not es_festival("Kraak & Smaak SOUNDSYSTEM") and not es_festival("Festus Banda")


def test_clave_festival():
    assert clave_festival("Pirata Festival 2026 Madrid") == clave_festival("Pirata Madrid Festival (Boikot, Evaristo)")
    assert clave_festival("Cadena 100 Por Ellas Festival 2026") == clave_festival("Cadena 100 Por Ellas 2026 festival")
    assert clave_festival("SANTUARIO Festival en Madrid - 2026 - SE APLAZA a 2027") == "santuario"
    assert clave_festival("Pirata Festival") != clave_festival("Galileo Rock Festival 2026")
    assert clave_festival("Hällas") == ""


def test_cartel_de_titulo():
    assert cartel_de_titulo("Pirata Madrid Festival (Boikot, Evaristo, benito Kamelas, Reincidentes y más)") == \
        ("Pirata Madrid Festival", ["Boikot", "Evaristo", "benito Kamelas", "Reincidentes"], True)
    assert cartel_de_titulo("Mad Psych Fest: KALEIDOBOLT y AXIOM9") == ("Mad Psych Fest", ["KALEIDOBOLT", "AXIOM9"], False)
    # no son carteles: un espectáculo, un dúo con '&', un artista con su ciclo
    assert cartel_de_titulo("MILLION DOLAR QUARTET: ELVIS PRESLEY, JOHNNY CASH, JERRY LEE LEWIS")[1] == []
    assert cartel_de_titulo("Layo & Bushwacka!")[1] == []
    assert cartel_de_titulo("JAZZ CON SABOR A CLUB 26: MININO BRAVO (Festival JazzMadrid)")[1] == []
    assert nombre_festival("SANTUARIO Festival en Madrid - 2026 - SE APLAZA a 2027") == "SANTUARIO Festival en Madrid - 2026"
