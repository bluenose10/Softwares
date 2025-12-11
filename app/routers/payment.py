"""Stripe payment integration for Pro subscriptions."""

import os
import stripe
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/api/payment", tags=["payment"])

# Initialize Stripe (API key from environment variable)
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PRICE_ID = os.getenv("STRIPE_PRICE_ID")

# Validate Stripe configuration
if not stripe.api_key:
    print("[WARNING] STRIPE_SECRET_KEY not set in environment variables")
if not STRIPE_PRICE_ID:
    print("[WARNING] STRIPE_PRICE_ID not set in environment variables")


@router.post("/create-checkout")
async def create_checkout_session(request: Request):
    """Create a Stripe Checkout session for Pro subscription."""
    try:
        # Get client IP for tracking
        client_ip = request.client.host

        print(f"[DEBUG] Creating checkout for IP: {client_ip}")
        print(f"[DEBUG] Stripe API Key: {stripe.api_key[:20]}...")
        print(f"[DEBUG] Price ID: {STRIPE_PRICE_ID}")

        # Create Stripe Checkout Session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': STRIPE_PRICE_ID,  # Your $9/month recurring price ID
                'quantity': 1,
            }],
            mode='subscription',  # Monthly recurring subscription
            success_url=f'{request.base_url}success?session_id={{CHECKOUT_SESSION_ID}}',
            cancel_url=f'{request.base_url}pricing',
            client_reference_id=client_ip,  # Store IP for webhook
            metadata={
                'client_ip': client_ip
            }
        )

        return JSONResponse({
            "checkout_url": checkout_session.url,
            "session_id": checkout_session.id
        })

    except Exception as e:
        print(f"[ERROR] Stripe checkout failed: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events (payment success, cancellation, etc.)."""
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')

    # Webhook secret from Stripe Dashboard
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")

    try:
        if webhook_secret:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
        else:
            # For testing without webhook secret
            import json
            event = json.loads(payload)

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']

        # Get client IP from metadata
        client_ip = session.get('metadata', {}).get('client_ip')

        if client_ip:
            # Set user to Pro status
            from app.services.usage_tracker import usage_tracker
            usage_tracker.set_pro_status(client_ip, True)

            print(f"✓ User {client_ip} upgraded to Pro!")

    elif event['type'] == 'customer.subscription.deleted':
        # Handle subscription cancellation
        subscription = event['data']['object']
        customer_id = subscription.get('customer')

        # TODO: Remove Pro status when canceled
        # Would need to store customer_id -> IP mapping in database
        print(f"⚠️ Subscription canceled for customer {customer_id}")

    return JSONResponse({"status": "success"})


@router.get("/success")
async def payment_success(request: Request, session_id: str = None):
    """Payment success page."""
    from fastapi.templating import Jinja2Templates

    templates = Jinja2Templates(directory="templates")

    # Set Pro status for this IP
    client_ip = request.client.host
    from app.services.usage_tracker import usage_tracker
    usage_tracker.set_pro_status(client_ip, True)

    return templates.TemplateResponse("success.html", {
        "request": request,
        "session_id": session_id
    })
