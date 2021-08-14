var fileInput = document.getElementById( 'upload' );

const caption_me = async () => {
    const file = fileInput.files[0];

    // handle file not found
    
    const data = new FormData();
    data.append('file', file);

    const processedImage = await fetch("/api/prepare",
        {
            method: 'POST',
            body: data
        }).then(response => {
            return response.json();
        }).then(result => {
            console.log(result)
            return result;
        });
};