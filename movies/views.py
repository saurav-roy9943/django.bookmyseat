from django.shortcuts import render, redirect ,get_object_or_404
from .models import Movie,Theater,Seat,Booking
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt


def movie_list(request):
    search_query = request.GET.get('search')
    if search_query:
        movies = Movie.objects.filter(name__icontains=search_query)
    else:
        movies = Movie.objects.all()

    paginator = Paginator(movies, 6) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'movies/movie_list.html', {
        'movies': page_obj,
        'page_obj': page_obj
    })

def theater_list(request,movie_id):
    movie = get_object_or_404(Movie,id=movie_id)
    theater=Theater.objects.filter(movie=movie)
    return render(request,'movies/theater_list.html',{'movie':movie,'theaters':theater})



@login_required(login_url='/login/')
def book_seats(request,theater_id):
    theaters=get_object_or_404(Theater,id=theater_id)
    seats=Seat.objects.filter(theater=theaters)
    if request.method=='POST':
        selected_Seats= request.POST.getlist('seats')
        error_seats=[]
        if not selected_Seats:
            return render(request,"movies/seat_selection.html",{'theater':theater,"seats":seats,'error':"No seat selected"})
        for seat_id in selected_Seats:
            seat=get_object_or_404(Seat,id=seat_id,theater=theaters)
            if seat.is_booked:
                error_seats.append(seat.seat_number)
                continue
            try:
                Booking.objects.create(
                    user=request.user,
                    seat=seat,
                    movie=theaters.movie,
                    theater=theaters,
                    price=seat.price  
                    )
                seat.is_booked=True
                seat.save()
            except IntegrityError:
                error_seats.append(seat.seat_number)
        if error_seats:
            error_message=f"The following seats are already booked:{',',join(error_seats)}"
            return render(request,'movies/seat_selection.html',{'theater':theater,"seats":seats,'error':"No seat selected"})
        return redirect('profile')
    return render(request,'movies/seat_selection.html',{'theaters':theaters,"seats":seats})

@login_required(login_url='/login/')
@require_POST
def cancel_booking(request):
    booking_id = request.POST.get('booking_id')
    try:
        booking = Booking.objects.get(id=booking_id, user=request.user)
        seat = booking.seat
        seat.is_booked = False
        seat.save()
        booking.delete()
        return JsonResponse({'success': True})
    except Booking.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Booking not found'})