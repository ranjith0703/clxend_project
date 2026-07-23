from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.database import engine, Base, get_db
from backend.models import User, Transaction, KYC, Wallet

from passlib.context import CryptContext
from jose import jwt, JWTError, ExpiredSignatureError

from datetime import datetime, timedelta
import time
import logging
import os


# ================= LOGGING =================

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    filename="logs/backend.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("wallet-backend")

logger.info("Wallet backend started")


# ================= FRONTEND LOGGING =================

frontend_logger = logging.getLogger("frontend")

frontend_logger.setLevel(logging.INFO)

frontend_handler = logging.FileHandler(
    "logs/frontend.log"
)

frontend_handler.setFormatter(
    logging.Formatter(
        "%(asctime)s | %(message)s"
    )
)

frontend_logger.addHandler(
    frontend_handler
)


# ================= INIT =================

Base.metadata.create_all(bind=engine)

app = FastAPI()


@app.get("/")
def home():

    logger.info("Home API accessed")

    return {
        "message": "FastAPI backend is running"
    }



# ================= CORS =================

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# ================= SECURITY =================

SECRET_KEY = "secret123"
ALGORITHM = "HS256"


pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)



# ================= SCHEMAS =================


class UserRegister(BaseModel):
    email: str
    password: str



class UserLogin(BaseModel):
    email: str
    password: str



class KYCRequest(BaseModel):
    govId: str



class TransactionSchema(BaseModel):
    receiver: str
    amount: int

class FrontendLog(BaseModel):

    action: str
    name: str
    email: str
    aadhaar: str    



class TransactionResponse(BaseModel):

    txHash: str
    amount: int
    sender: str
    recipient: str
    status: str
    timestamp: str

    class Config:
        from_attributes = True




# ================= HELPERS =================


def hash_password(password: str):

    return pwd_context.hash(password[:72])



def verify_password(password, hashed):

    return pwd_context.verify(
        password[:72],
        hashed
    )



def create_token(user_id: int):

    payload = {

        "user_id": user_id,

        "exp":
        datetime.utcnow()
        + timedelta(hours=1)

    }


    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )



def verify_token(
    authorization: str = Header(None)
):

    if not authorization:

        logger.warning(
            "Authorization token missing"
        )

        raise HTTPException(
            status_code=401,
            detail="Token missing"
        )


    try:

        token = authorization.split(" ")[1]


        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )


        user_id = payload.get("user_id")


        return user_id



    except ExpiredSignatureError:

        logger.warning(
            "Expired token used"
        )

        raise HTTPException(
            status_code=401,
            detail="Token expired"
        )



    except JWTError:

        logger.warning(
            "Invalid token"
        )

        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )




# ================= AUTH =================



@app.post("/auth/register")
def register(
    user: UserRegister,
    db: Session = Depends(get_db)
):

    existing = db.query(User).filter(
        User.email == user.email
    ).first()


    if existing:

        logger.warning(
            f"Registration failed existing user {user.email}"
        )

        raise HTTPException(
            status_code=400,
            detail="User already exists"
        )



    new_user = User(

        email=user.email,

        password=
        hash_password(user.password)

    )


    db.add(new_user)

    db.commit()

    db.refresh(new_user)



    wallet = Wallet(

        user_id=new_user.id,

        balance=5000,

        wallet_address=
        "0x"
        + str(new_user.id).zfill(10),

        did=
        f"did:wallet:{new_user.id}",

        blockchain="Polygon"

    )


    db.add(wallet)

    db.commit()



    logger.info(
        f"New user registered {user.email}"
    )


    return {

        "success": True,

        "message":
        "Registered successfully"

    }





@app.post("/auth/login")
def login(
    user: UserLogin,
    db: Session = Depends(get_db)
):


    db_user = db.query(User).filter(
        User.email == user.email
    ).first()



    if not db_user or not verify_password(
        user.password,
        db_user.password
    ):

        logger.warning(
            f"Login failed {user.email}"
        )

        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )



    token = create_token(
        db_user.id
    )


    logger.info(
        f"Login success {user.email}"
    )



    return {

        "success": True,

        "message":
        "Login successful",

        "token": token,

        "user": {

            "id": db_user.id,

            "email": db_user.email

        }

    }



# ================= FRONTEND LOG API =================


@app.post("/frontend-log")
def create_frontend_log(data: FrontendLog):

    frontend_logger.info(
        f"ACTION={data.action} | "
        f"NAME={data.name} | "
        f"EMAIL={data.email} | "
        f"AADHAAR={data.aadhaar}"
    )

    return {
        "status": "logged"
    }


# ================= KYC =================



@app.post("/kyc/submit")
def submit_kyc(
    data: KYCRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(verify_token)
):

    try:


        kyc = KYC(

            user_id=user_id,

            gov_id=data.govId,

            status="Pending"

        )


        db.add(kyc)

        db.commit()



        logger.info(
            f"KYC submitted user {user_id}"
        )



        return {

            "message":
            "KYC submitted",

            "status":
            "Approved"

        }



    except Exception as e:


        logger.error(
            str(e)
        )


        raise HTTPException(

            status_code=500,

            detail=str(e)

        )






# ================= TRANSACTIONS =================



@app.post(
    "/send",
    response_model=TransactionResponse
)
def send_transaction(

    tx: TransactionSchema,

    db: Session = Depends(get_db),

    user_id: int = Depends(verify_token)

):


    new_tx = Transaction(

        txHash=
        "0x"
        + str(int(time.time())),

        amount=tx.amount,

        sender="You",

        recipient=tx.receiver,

        status="Confirmed",

        timestamp=
        time.strftime(
            "%Y-%m-%d %H:%M:%S"
        ),

        user_id=user_id

    )


    db.add(new_tx)

    db.commit()

    db.refresh(new_tx)



    logger.info(
        f"Transaction created {new_tx.txHash}"
    )


    return new_tx






@app.get(
    "/transactions",
    response_model=list[TransactionResponse]
)

def get_transactions(

    db: Session = Depends(get_db),

    user_id: int = Depends(verify_token)

):


    logger.info(
        f"Transactions fetched user {user_id}"
    )


    return db.query(Transaction).filter(
        Transaction.user_id == user_id
    ).all()





# ================= BALANCE =================


@app.get("/balance")
def balance():

    logger.info(
        "Balance API accessed"
    )


    return {

        "balance":5000

    }





# ================= WALLET =================



@app.get("/wallet")
def get_wallet(

    db: Session = Depends(get_db),

    user_id: int = Depends(verify_token)

):


    user = db.query(User).filter(
        User.id == user_id
    ).first()



    if not user:

        raise HTTPException(
            status_code=404,
            detail="User not found"
        )



    wallet = db.query(Wallet).filter(
        Wallet.user_id == user_id
    ).first()



    if not wallet:

        raise HTTPException(
            status_code=404,
            detail="Wallet not found"
        )



    logger.info(
        f"Wallet fetched user {user_id}"
    )



    return {


        "userId": user.id,

        "email": user.email,

        "phone":
        "9876543210",

        "walletId":
        f"WLT-{user.id}",

        "walletAddress":
        wallet.wallet_address,

        "balance":
        wallet.balance,

        "did":
        wallet.did,

        "blockchain":
        wallet.blockchain,

        "identityStatus":
        "verified",

        "txHash":
        "0x"
        + str(user.id).zfill(12)

    }