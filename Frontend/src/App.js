import React, { useState } from "react";

const App = () => {
    const [image, setImage] = useState(null);
    const [title, setTitle] = useState("");
    const [description, setDescription] = useState("");
    const [outputImages, setOutputImages] = useState([]);
    const [loading, setLoading] = useState(false);

    // Handle file input change
    const handleFileChange = (event) => {
        setImage(event.target.files[0]);
    };

    // Upload the image and request the generation of posters
    const uploadAndGenerate = async () => {
        if (!image) {
            alert("Please select an image first.");
            return;
        }
    
        setLoading(true);
        const formData = new FormData();
        formData.append("image", image);
    
        try {
            // Update the URL to match the backend route
            const response = await fetch("http://localhost:5001/generate_posters", {
                method: "POST",
                body: formData
            });
    
            const data = await response.json();
            console.log("Backend Response:", data);
    
            if (!response.ok) throw new Error(data.error || "Unknown error occurred");
    
            setTitle(data.title);
            setDescription(data.description);
            setOutputImages(data.output_files);
        } catch (error) {
            console.error("Error uploading image:", error);
            alert("Upload failed: " + error.message);
        } finally {
            setLoading(false);
        }
    };
    
    return (
        <div style={{ textAlign: "center", fontFamily: "Arial, sans-serif", padding: "20px" }}>
            <h1>Dynamic Book Poster Generator</h1>

            {/* File input for image */}
            <input
                type="file"
                accept="image/*"
                onChange={handleFileChange}
                style={{ padding: "10px", fontSize: "16px" }}
            /><br/>

            {/* Button to trigger the poster generation */}
            <button
                onClick={uploadAndGenerate}
                disabled={loading}
                style={{ marginTop: "10px", padding: "10px", fontSize: "16px" }}
            >
                {loading ? "Generating..." : "Generate Posters"}
            </button>

            {/* Display the generated title and description */}
            {title && <h2 style={{ marginTop: "20px" }}>{title}</h2>}
            {description && <p style={{ fontSize: "18px", fontStyle: "italic" }}>{description}</p>}

            {/* Display Generated Posters */}
            <div
                style={{
                    marginTop: "20px",
                    display: "flex",
                    flexWrap: "wrap",
                    justifyContent: "center",
                    gap: "20px"
                }}
            >
                {outputImages.map((image, index) => (
                    <div key={index} style={{ textAlign: "center" }}>
                        <h3>Poster {index + 1}</h3>
                        <img
                            src={`http://localhost:5001/static/output/${image}`}
                            alt={`Poster ${index + 1}`}
                            style={{
                                width: "100%",
                                maxWidth: "400px",
                                border: "2px solid #ccc",
                                boxShadow: "2px 2px 10px rgba(0,0,0,0.2)",
                                borderRadius: "10px"
                            }}
                        />
                    </div>
                ))}
            </div>
        </div>
    );
};

export default App;
