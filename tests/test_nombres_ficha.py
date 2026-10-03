

def test_n3_nombres_en_titulos():
    from scraper.nombres import claves_ficha
    c = lambda t: claves_ficha({"artista": t, "categorias": []})
    assert "CLAUDIA CRUZ" in c("ESPECTÁCULO FLAMENCO: CLAUDIA CRUZ")
    assert "PAULA MORENO" in c("ESPECTÁCULO FLAMENCO: PAULA MORENO Y BARTOLO AL BAILE")
    assert c("CUBAN BRUNCH: PEPE Y SU TUMBAO")[1:] == ["PEPE Y SU TUMBAO"]  # nunca "PEPE" a secas
    assert "INOIDEL GONZÁLEZ" in c("INOIDEL GONZÁLEZ QUARTET")
    assert "Yasuharu Takanashi" in c("Yasuharu Takanashi’s")
    assert "FRUIT TONES" in c("HALLOWEEN! FRUIT TONES")
    assert "Apolo Brass" in c("DIA DE LA HISPANIDAD. MÚSICA. 'Apolo Brass', presenta 'Aires de América'")
    assert c("Tributo a Taylor Swift. Candlelight") == ["Tributo a Taylor Swift. Candlelight"]
