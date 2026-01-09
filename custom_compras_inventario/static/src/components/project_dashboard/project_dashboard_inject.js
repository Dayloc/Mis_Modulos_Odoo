/** @odoo-module **/

import { rpc } from "@web/core/network/rpc";

console.log("🔥 SCRIPT CARGADO");

function getProjectIdFromUrl() {
    const match = window.location.pathname.match(/\/project\/(\d+)/);
    return match ? parseInt(match[1], 10) : null;
}

function injectButton() {
    const box = document.querySelector(".o_rightpanel_data .oe_button_box");
    if (!box) return false;

    if (box.querySelector(".custom_test_button")) return true;


    const btn = document.createElement("button");
    btn.className =
        "btn btn-danger h-auto py-2 border border-start-0 border-top-0 " +
        "text-center rounded-0 oe_stat_button custom_test_button";

    btn.innerHTML = `
        <div class="o_stat_info ">
            <span class="o_stat_text">Gastos del Proyecto</span>
        </div>
    `;


    const container = document.createElement("div");
    container.className = "custom_expenses_container";
    container.style.marginTop = "12px";
    container.style.width = "100%";


    btn.addEventListener("click", async () => {
        const projectId = getProjectIdFromUrl();


        try {
            const result = await rpc(
                "/web/dataset/call_kw/project.project/get_purchase_expenses",
                {
                    model: "project.project",
                    method: "get_purchase_expenses",
                    args: [projectId],
                    kwargs: {},
                }
            );



            container.innerHTML = "";


            const table = document.createElement("table");
            table.style.width = "100%";
            table.style.borderCollapse = "collapse";


            table.innerHTML = `
                <thead class="border-amber">
                    <tr>
                        <th class="text-danger" style="text-align:left;">Documento</th>
                        <th class="text-danger" style="text-align:left;">Producto</th>
                        <th class="text-danger" style="text-align:right;">Cantidad</th>
                        <th class="text-danger" style="text-align:right;">Precio unit.</th>
                        <th class="text-danger" style="text-align:right;">Total línea</th>
                    </tr>
                </thead>
            `;

            // CUERPO
            const tbody = document.createElement("tbody");

            result.lines.forEach(line => {
                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td>${line.document}</td>
                    <td>${line.product}</td>
                    <td style="text-align:right;">${line.qty} unit</td>
                    <td style="text-align:right;">${line.price_unit} €</td>
                    <td style="text-align:right;">${line.line_total} €</td>
                `;
                tbody.appendChild(tr);
            });

            // FILA TOTAL
            const totalRow = document.createElement("tr");
            totalRow.innerHTML = `
                <td colspan="4" style="text-align:right;"><strong class="text-danger">Total</strong></td>
                <td style="text-align:right;"><strong>${result.total} €</strong></td>
               
            `;
            tbody.appendChild(totalRow);

            table.appendChild(tbody);
            container.appendChild(table);

        } catch (error) {
            console.error(" Error llamando al backend:", error);
        }
    });

    // INSERTAR EN EL DOM
    box.appendChild(btn);
    box.parentElement.appendChild(container);


    return true;
}
let lastUrl = location.href;

function watchNavigation() {
    if (location.href !== lastUrl) {
        lastUrl = location.href;

        // Esperamos a que Odoo renderice la vista
        setTimeout(() => {
            injectButton();
        }, 300);
    }

    requestAnimationFrame(watchNavigation);
}

// Inyección inicial
injectButton();

// Vigilar navegación SPA de Odoo
watchNavigation();

