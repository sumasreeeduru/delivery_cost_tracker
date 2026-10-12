from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
import heapq

@dataclass
class Driver:
    driver_id: str
    usd_hourly_rate: Decimal
    
class DeliveryStatus(Enum):
    DELIVERED = "delivered"
    PAID = "paid"
    
@dataclass
class Delivery:
    delivery_id: int
    driver_id: str
    start_time: int  # Seconds
    end_time: int  # Seconds
    cost: Decimal  # Frozen when recorded
    status: DeliveryStatus = DeliveryStatus.DELIVERED
    
class DeliveryCostTracker:
    def __init__(self):
        self.drivers: dict[str, Driver] = {}
        self.deliveries: dict[int, Delivery] = {}
        self.unpaid_deliveries: list[tuple[int, int]] = []  # (end_time, delivery_id)

        self._next_delivery_id = 1
        self._total_cost = Decimal("0.000")
        self._total_paid_cost = Decimal("0.000")
        
        
    def add_driver(self, driver_id: str, usd_hourly_rate: Decimal) -> None:
        if not self._validate_driver(driver_id, usd_hourly_rate):
            return

        self.drivers[driver_id] = Driver(driver_id, usd_hourly_rate)
    
    def record_delivery(
        self, driver_id: str, start_time: int, end_time: int
    ) -> int | None:
        if not self._validate_delivery(driver_id, start_time, end_time):
            return None

        duration_seconds = end_time - start_time
        cost = self._calculate_delivery_cost(driver_id, duration_seconds)

        delivery_id = self._next_delivery_id
        delivery = Delivery(
            delivery_id=delivery_id,
            driver_id=driver_id,
            start_time=start_time,
            end_time=end_time,
            cost=cost,
        )

        self.deliveries[delivery_id] = delivery
        heapq.heappush(self.unpaid_deliveries, (end_time, delivery_id))
        self._total_cost += cost
        self._next_delivery_id += 1
        return delivery_id

    def pay_upto_time(self, time: int) -> None:
        if not isinstance(time, int) or isinstance(time, bool):
            print("Timestamp is incorrect; time must be integer seconds.")
            return

        while self.unpaid_deliveries and self.unpaid_deliveries[0][0] <= time:
            _, delivery_id = heapq.heappop(self.unpaid_deliveries)
            delivery = self.deliveries[delivery_id]

            if delivery.status == DeliveryStatus.DELIVERED:
                delivery.status = DeliveryStatus.PAID
                self._total_paid_cost += delivery.cost
                
    def get_unpaid_cost(self) -> Decimal:
        unpaid_cost = self._total_cost - self._total_paid_cost
        return unpaid_cost.quantize(Decimal("0.01"))
    
    def get_drivers_active_in_previous_24_hours(
        self, time: int
    ) -> set[str] | None:
        if not isinstance(time, int) or isinstance(time, bool):
            print("Timestamp is incorrect; time must be integer seconds.")
            return None

        window_start = time - 24 * 60 * 60

        return {
            delivery.driver_id
            for delivery in self.deliveries.values()
            if delivery.start_time < time and delivery.end_time > window_start
        }
    
    #helper functions
    def _calculate_delivery_cost(
        self, driver_id: str, duration_seconds: int
    ) -> Decimal:
        hourly_rate = self.drivers[driver_id].usd_hourly_rate
        cost = hourly_rate * Decimal(duration_seconds) / Decimal(3600)
        return cost.quantize(Decimal("0.001"))
    
    
    #Validations
    def _validate_driver(self, driver_id: str, usd_hourly_rate: Decimal) -> bool:
        if not isinstance(driver_id, str):
            print("Driver ID must be a string.")
            return False

        if driver_id in self.drivers:
            print(f"Driver '{driver_id}' already exists.")
            return False

        if (
            not isinstance(usd_hourly_rate, Decimal)
            or not usd_hourly_rate.is_finite()
            or usd_hourly_rate <= 0
        ):
            print("Hourly rate must be a finite Decimal greater than zero.")
            return False

        return True

    def _validate_delivery(
        self, driver_id: str, start_time: int, end_time: int
    ) -> bool:
        if (
            not isinstance(start_time, int)
            or isinstance(start_time, bool)
            or not isinstance(end_time, int)
            or isinstance(end_time, bool)
        ):
            print("Timestamp is incorrect; timestamps must be integer seconds.")
            return False

        if not isinstance(driver_id, str) or driver_id not in self.drivers:
            print(f"Driver '{driver_id}' does not exist.")
            return False

        duration = end_time - start_time

        if duration <= 0:
            print("Delivery duration must be greater than zero.")
            return False

        if duration > 3 * 60 * 60:
            print("Cannot insert delivery: duration exceeds 3 hours.")
            return False

        return True

def process_operations(operations: list[list[str]]) -> list[str]:
    tracker = DeliveryCostTracker()
    results: list[str] = []

    for operation in operations:
        if not operation:
            print("Invalid operation.")
            continue

        name = operation[0]

        if name == "ADD_DRIVER" and len(operation) == 3:
            try:
                rate = Decimal(operation[2])
            except Exception:
                print("Hourly rate is incorrect.")
                continue

            tracker.add_driver(operation[1], rate)

        elif name == "RECORD_DELIVERY" and len(operation) == 4:
            try:
                start_time = int(operation[2])
                end_time = int(operation[3])
            except ValueError:
                print("Timestamp is incorrect; timestamps must be integer seconds.")
                continue

            tracker.record_delivery(operation[1], start_time, end_time)

        elif name == "GET_TOTAL_COST" and len(operation) == 1:
            total = tracker._total_cost.quantize(Decimal("0.01"))
            results.append(f"{total:.2f}")

        elif name == "GET_UNPAID_COST" and len(operation) == 1:
            results.append(f"{tracker.get_unpaid_cost():.2f}")

        elif name == "PAY_UP_TO" and len(operation) == 2:
            try:
                time = int(operation[1])
            except ValueError:
                print("Timestamp is incorrect; time must be integer seconds.")
                continue

            tracker.pay_upto_time(time)

        else:
            print(f"Invalid operation: {operation}")

    return results


if __name__ == "__main__":
    operations = [["ADD_DRIVER","a","10.00"],["ADD_DRIVER","b","20.00"],["RECORD_DELIVERY","a","100","1300"],["RECORD_DELIVERY","a","110","1300"],["RECORD_DELIVERY","b","500","2300"],["GET_TOTAL_COST"],["PAY_UP_TO","1500"],["GET_UNPAID_COST"]]

    print(process_operations(operations))




    
    
"""
Driver = {driverid: usd_hourly_rates}
 - repeat driverid is not allowed
 - update shouldn't change the exisiting delviery records
 
Delivery 
 - driverid
 - start_time
 - end_time
 - status (delivered,paid)
 - cost 
 
 - we shouldn't add a delivery if the completion exceeds 3 hours. then what to do?
 - single driver has overlapping deliveries - each delivery is paid independently

DeliveryCostTracker:
    - list of deliveries in hashmap {delieryid : Delivery}
    -totalcostofdeliveries
    - minheap of deliveries based on endtime to get the unpaid deliveries
    - totalpaidcostofdeliveries
 
addDriver:
    - adds into the driver dictionary 
    
recordDelivery:
    - add Delivery into list of deliveries
    - calculate the cost and insert
    - update tehe total cost of deliveries
    

GetTotalCost
    - **iterate through the list of deliveries and calculate the total cost based on the driver rates and delivery durations. O(D)**
    - fetch the gettotalcost of deliveries from the company class
 
payUptoTime(time):
    - **iterate through the list of deliveries and mark the delivery with endTime<=aytime as paid**
    - pop from min heap where endtime <= time and mark the delivery as paid
    - update the total paid cost of deliveries in the company class

getunpaidcost:
    - **iterate through the list of deliveries and calculate the total cost for unpaid deliveries**
    - fetch the totalcostofdeliveries - totalpaidcostofdeliveries from the company class

"""
