def test_login_usuario_inexistente(client):
    """Verifica que un usuario no registrado reciba error 401."""
    respuesta = client.post(
        "/usuarios/login",
        data={"username": "usuario_fantasma", "password": "password123"}
    )
    assert respuesta.status_code == 401
    assert "detail" in respuesta.json()