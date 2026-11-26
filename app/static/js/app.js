/* VetSystem - interações da interface. Todas as telas funcionam sem este arquivo;
   ele só deixa o uso mais confortável. */
(function () {
    "use strict";

    var body = document.body;

    function each(selector, callback, root) {
        Array.prototype.forEach.call((root || document).querySelectorAll(selector), callback);
    }

    /* Opção vazia dos selects: o texto padrão do Django nem sempre vem traduzido */
    var translateBlank = function (root) {
        each("select option[value='']", function (option) {
            if (/^-+$|select an option/i.test(option.textContent.trim())) {
                option.textContent = "Selecione uma opção";
            }
        }, root);
    };
    translateBlank(document);

    /* Menu lateral no celular */
    var menu = document.getElementById("menu");
    var opener = document.querySelector("[data-menu-open]");

    function setMenu(open) {
        body.classList.toggle("menu-open", open);
        if (opener) {
            opener.setAttribute("aria-expanded", String(open));
        }
        if (open && menu) {
            var target = menu.querySelector("[data-menu-close]");
            // espera a gaveta ficar visível antes de mover o foco
            window.setTimeout(function () { if (target) { target.focus(); } }, 60);
        }
    }

    if (opener) {
        opener.addEventListener("click", function () { setMenu(true); });
    }

    each("[data-menu-close]", function (el) {
        el.addEventListener("click", function () {
            setMenu(false);
            if (opener) { opener.focus(); }
        });
    });

    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape" && body.classList.contains("menu-open")) {
            setMenu(false);
            if (opener) { opener.focus(); }
        }
    });

    /* Fechar avisos */
    each("[data-dismiss]", function (button) {
        button.hidden = false;
        button.addEventListener("click", function () {
            button.closest(".alert").remove();
        });
    });

    /* Mostrar ou ocultar a senha */
    each("input[type='password']", function (input) {
        var control = input.closest("[data-password]");
        if (!control) { return; }

        var button = control.querySelector(".reveal");
        var use = button.querySelector("use");
        button.hidden = false;

        button.addEventListener("click", function () {
            var show = input.type === "password";
            input.type = show ? "text" : "password";
            button.setAttribute("aria-pressed", String(show));
            button.setAttribute("aria-label", show ? "Ocultar senha" : "Mostrar senha");
            use.setAttribute("href", use.getAttribute("href").replace(/#.*/, show ? "#eye-off" : "#eye"));
        });
    });

    /* Selects que enviam o formulário ao mudar */
    each("select[data-autosubmit]", function (select) {
        select.addEventListener("change", function () { select.form.submit(); });
    });

    /* Confirmação antes de ações sensíveis (ex.: estorno) */
    var dialog = document.getElementById("confirm-dialog");

    each("form[data-confirm]", function (form) {
        form.addEventListener("submit", function (event) {
            var message = form.getAttribute("data-confirm");

            if (!dialog || typeof dialog.showModal !== "function") {
                if (!window.confirm(message)) { event.preventDefault(); }
                return;
            }

            event.preventDefault();
            dialog.querySelector("[data-confirm-title]").textContent = form.getAttribute("data-confirm-title");
            dialog.querySelector("[data-confirm-text]").textContent = message;
            dialog.querySelector("[data-confirm-yes]").textContent = form.getAttribute("data-confirm-action");
            dialog.returnValue = "";
            dialog.onclose = function () {
                // form.submit() não dispara este evento de novo
                if (dialog.returnValue === "yes") { form.submit(); }
            };
            dialog.showModal();
        });
    });

    /* Materiais do atendimento: adicionar e remover linhas do formset */
    var formset = document.querySelector("[data-formset]");

    if (formset) {
        var prefix = formset.getAttribute("data-formset");
        var total = document.getElementById("id_" + prefix + "-TOTAL_FORMS");
        var list = formset.querySelector("[data-formset-list]");
        var template = formset.querySelector("template");
        var emptyMessage = formset.querySelector("[data-formset-empty]");

        var bindRow = function (row) {
            var checkbox = row.querySelector("input[type='checkbox'][name$='-DELETE']");
            var button = row.querySelector("[data-formset-remove]");
            if (!checkbox || !button) { return; }

            var use = button.querySelector("use");
            var label = button.querySelector(".icon-btn__text");

            var render = function () {
                var removed = checkbox.checked;
                row.classList.toggle("is-removed", removed);
                label.textContent = removed ? "Desfazer" : "Remover";
                use.setAttribute("href", use.getAttribute("href").replace(/#.*/, removed ? "#undo-2" : "#trash-2"));
                button.classList.toggle("icon-btn--danger", !removed);
            };

            button.addEventListener("click", function () {
                checkbox.checked = !checkbox.checked;
                render();
            });
            render();
        };

        each(".item-row", bindRow, list);

        each("[data-formset-add]", function (button) {
            button.hidden = false;
            button.addEventListener("click", function () {
                var index = parseInt(total.value, 10);
                var html = template.innerHTML.replace(/__prefix__/g, index);
                list.insertAdjacentHTML("beforeend", html);
                total.value = index + 1;
                if (emptyMessage) { emptyMessage.hidden = true; }
                var row = list.lastElementChild;
                translateBlank(row);
                bindRow(row);
                var select = row.querySelector("select");
                if (select) { select.focus(); }
            });
        });
    }

    /* Emissão de fatura: soma dos atendimentos marcados */
    var invoice = document.querySelector("[data-invoice]");

    if (invoice) {
        var checks = invoice.querySelectorAll("input[name='atendimentos']");
        var all = invoice.querySelector("[data-check-all]");
        var output = invoice.querySelector("[data-total]");
        var quantity = invoice.querySelector("[data-quantity]");
        var submit = invoice.querySelector("button[type='submit']");

        var update = function () {
            var sum = 0;
            var selected = 0;
            Array.prototype.forEach.call(checks, function (check) {
                if (check.checked) {
                    sum += parseFloat(check.getAttribute("data-valor"));
                    selected += 1;
                }
            });
            output.textContent = sum.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
            quantity.textContent = selected === 1 ? "1 atendimento selecionado" : selected + " atendimentos selecionados";
            all.checked = selected === checks.length;
            all.indeterminate = selected > 0 && selected < checks.length;
            submit.disabled = selected === 0;
        };

        Array.prototype.forEach.call(checks, function (check) {
            check.addEventListener("change", update);
        });

        all.addEventListener("change", function () {
            Array.prototype.forEach.call(checks, function (check) { check.checked = all.checked; });
            update();
        });

        update();
        // o navegador pode restaurar as caixas ao voltar para a página
        window.addEventListener("pageshow", update);
    }
}());
