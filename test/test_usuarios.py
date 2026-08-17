def test_login_usuario_inexistente(client):
    """Verifica que un usuario no registrado reciba error 401."""
    respuesta = client.post(
        "/usuarios/login",
        data={"username": "usuario_fantasma", "password": "password123"}
    )
    assert respuesta.status_code == 401
    assert "detail" in respuesta.json()
    
def test_no_se_puede_deshabilitar_ni_renombrar_admin(client, override_admin):
    admin_id = override_admin.id

    # 1. Intentar cambiar el username de 'admin' debe fallar (400)
    res_rename = client.put(f"/usuarios/{admin_id}", json={"username": "super_admin"})
    assert res_rename.status_code == 400
    assert "No está permitido modificar el nombre" in res_rename.json()["detail"]

    # 2. Intentar deshabilitar al usuario 'admin' debe fallar (400)
    res_toggle = client.patch(f"/usuarios/{admin_id}/estado")  # 👈 Endpoint correcto
    assert res_toggle.status_code == 400
    assert "No se puede deshabilitar" in res_toggle.json()["detail"]