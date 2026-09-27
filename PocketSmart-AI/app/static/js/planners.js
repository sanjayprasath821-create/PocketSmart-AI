function addItem() {
    const container =
        document.getElementById("items");

    const item =
        document.createElement("div");

    item.className = "item";

    item.innerHTML = `
        <input
            name="cat"
            placeholder="Dining table"
        >

        <input
            name="qty"
            type="number"
            min="1"
            value="1"
        >
    `;

    container.appendChild(item);
}


document.addEventListener(
    "DOMContentLoaded",
    () => {

        const form =
            document.querySelector(
                'form[action="/generate-home"]'
            );

        if (!form) {
            return;
        }


        form.addEventListener(
            "submit",
            () => {

                const items = [
                    ...document.querySelectorAll(
                        "#items .item"
                    )
                ]

                .map(
                    (item) => ({
                        category:
                            item
                                .querySelector(
                                    "[name=cat]"
                                )
                                .value
                                .trim(),

                        quantity:
                            Number(
                                item
                                    .querySelector(
                                        "[name=qty]"
                                    )
                                    .value
                            ) || 1,
                    })
                )

                .filter(
                    (item) => item.category
                );


                document.getElementById(
                    "items_json"
                ).value =
                    JSON.stringify(items);
            }
        );
    }
);