"""Unit tests for axiom.email.exception hierarchy."""

from axiom.core.exceptions import BaseError
from axiom.email.exception import (
    AxiomEmailError,
    EmailConfigError,
    EmailRenderError,
    EmailSendError,
)


def test_axiom_email_error_is_base_error():
    assert issubclass(AxiomEmailError, BaseError)


def test_email_send_error_hierarchy():
    assert issubclass(EmailSendError, AxiomEmailError)
    assert issubclass(EmailSendError, BaseError)


def test_email_config_error_hierarchy():
    assert issubclass(EmailConfigError, AxiomEmailError)


def test_email_render_error_hierarchy():
    assert issubclass(EmailRenderError, AxiomEmailError)


def test_can_instantiate_with_message():
    err = AxiomEmailError("something went wrong")
    assert err.message == "something went wrong"
    assert str(err) == "something went wrong"


def test_code_attribute():
    assert AxiomEmailError.code == "email_error"
    assert EmailSendError.code == "email_send_error"
    assert EmailConfigError.code == "email_config_error"
    assert EmailRenderError.code == "email_render_error"
