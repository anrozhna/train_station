# 🚆 Railway Station Management System

## Features

- **Train Management**: Create and manage train types and individual trains.  
- **Crew Management**: Add, update, and assign crew members to specific journeys.  
- **Station Management**: Manage railway stations, including their geolocation (latitude and longitude).  
- **Route Management**: Define and validate travel routes between stations.  
- **Journey Management**: Organize train journeys along routes and manage their schedules.  
- **Ticket Booking**: Book seats for train journeys and check seat availability.  
- **Order Management**: Handle user orders for reserved tickets.  
- **Authentication**: Secure API endpoints for authenticated users and administrators.  
- Users can only access their own orders and tickets.  
- Everyone can view occupied seats for a given journey.  
- **Filtering**: Search and filter journeys by route, departure time, and arrival time.  

> JWT Token-based authentication is used in this project.

---

## Overview

This application offers functionality for:

- Managing trains, crews, stations, routes, and journeys  
- Creating and maintaining routes for train journeys  
- Handling ticket reservations and user orders  

---

## Installation

```bash
docker-compose build
docker-compose up

