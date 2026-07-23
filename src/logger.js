import axios from "axios";


const LOG_API = "http://localhost:8000/frontend-log";


export const sendFrontendLog = async (data) => {

    try {

        await axios.post(
            LOG_API,
            data
        );

    } catch(error) {

        console.log(
            "Frontend log error",
            error
        );

    }

};