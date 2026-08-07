document.addEventListener("DOMContentLoaded", () => {
    const btn = document.querySelector("a[href='scan.html']");
    
    if (btn) {
        btn.addEventListener("click", () => {
            console.log("Opening scanner...");
        });
    }
});