def test_basic_functionality():
    """Test básico para verificar que pytest funciona"""
    assert True

def test_simple_math():
    """Test simple de matemáticas"""
    assert 2 + 2 == 4
    assert 5 * 5 == 25

def test_string_operations():
    """Test de operaciones con strings"""
    text = "Hello World"
    assert len(text) == 11
    assert "Hello" in text
