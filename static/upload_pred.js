var fileInput = document.getElementById( 'upload' );
var mess = document.getElementById('message');

var auto_reload;
var total;

const reload_result = async (job_id) => {    
    const res = await fetch("/api/v1/results/" + job_id,
    {
        method: 'GET'
    }).then(response => {
        return response.json();
    }).then(result => {
        console.log(result);
        mess.textContent = JSON.stringify(result);
        if (result.status === 'completed') {
            clearInterval(auto_reload);
        }

        return result;
    });

    return res;
};

const caption_me = async () => {
    const file = fileInput.files[0];

    // handle file not found
    
    const data = new FormData();
    data.append('file', file);

    const processedImage = await fetch("/api/v1/captionme",
        {
            method: 'POST',
            body: data
        }).then(response => {
            return response.json();
        }).then(result => {
            console.log(result);
            mess.textContent = JSON.stringify(result);
            
            total = result;

            const job_id = result.result.job_id;
            auto_reload = setInterval(reload_result(job_id), 1000);

            return result;
        });
};