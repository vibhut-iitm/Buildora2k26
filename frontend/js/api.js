const API_URL = "http://127.0.0.1:5000";

async function verifyToken(token) {
    try {
        const response = await fetch(`${API_URL}/verify`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ token: token })
        });

        const data = await response.json();
        return data;
    } catch (error) {
        return { status: "error" };
    }
}