# Step 2: Introduction & Business Application

**Goal:** Prove to the panel that you have built a working business application that solves the problem statement *before* diving into the DevOps configurations.

## What you are doing on screen:
1. Show the main **FinSight Dashboard** in your browser.
2. Click on the **Risk Calculator** tab in the sidebar.
3. Type `5000` into the Amount box.
4. Select `TRADE` from the dropdown.
5. Click **Calculate Risk Score**.

## What you should say exactly:
> "Good morning panel. This is FinSight, the Real-Time Financial Risk Analytics Platform built for Case Study 53. 
> 
> The prompt required us to solve the issue of delayed risk calculations caused by legacy applications. To solve this, I completely re-architected the system into a modern microservices pattern. 
> 
> What you are seeing here is the React frontend. When I submit this risk calculation, it hits our **Analytics API Gateway** (built in FastAPI), which then asynchronously delegates the heavy mathematical computation to our **Risk Engine** microservice.
> 
> As you can see, the latency is extremely low (point to the Engine Latency on the screen), and it instantly generates a dynamic risk score based on simulated real-time market volatility."

---
**Next Step -> Open `03_AutoScaling.md`**
