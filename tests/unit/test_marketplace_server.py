import pytest
import pytest
from servers.marketplace_server import install_component, verify_component, update_component, InstallationRequest, VerificationRequest, UpdateRequest

@pytest.mark.asyncio
async def test_install_component():
    request_data = InstallationRequest(
        component_name="test_component",
        version="1.0.0",
        installation_path="/tmp/test_install"
    )
    result = await install_component(request_data)
    assert result == {"message": "Component test_component v1.0.0 installed successfully at /tmp/test_install"}

@pytest.mark.asyncio
async def test_verify_component():
    request_data = VerificationRequest(
        component_name="test_component",
        version="1.0.0",
        checksum="some_checksum",
        installation_path="/tmp/test_install"
    )
    result = await verify_component(request_data)
    assert result == {"message": "Component test_component v1.0.0 verified successfully"}

@pytest.mark.asyncio
async def test_update_component():
    request_data = UpdateRequest(
        component_name="test_component",
        current_version="1.0.0",
        new_version="1.0.1",
        installation_path="/tmp/test_install"
    )
    result = await update_component(request_data)
    assert result == {"message": "Component test_component updated from v1.0.0 to v1.0.1 successfully"}