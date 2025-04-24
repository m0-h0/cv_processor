import { Component, OnInit } from "@angular/core";
import { HttpClient, HttpHeaders, HttpParams } from "@angular/common/http";
import { FormsModule } from "@angular/forms";
import { CommonModule } from "@angular/common";
import { catchError, tap } from "rxjs/operators";
import { of } from "rxjs";
import { AuthService } from "./auth.service";
import { environment } from "../environments/environment";

interface Job {
  id: number;
  file_key: string;
  result_key: string | null;
  status: string;
  created_at: string;
  updated_at: string | null;
  download_url?: string;
}

@Component({
  selector: "app-root",
  imports: [CommonModule, FormsModule],
  templateUrl: "./app.component.html",
  styleUrls: ["./app.component.css"],
})
export class AppComponent implements OnInit {
  jobs: Job[] = [];
  selectedFile: File | null = null;
  username = "";
  password = "";
  email = "";
  isRegisterMode = false;

  constructor(private http: HttpClient, private authService: AuthService) {}

  ngOnInit() {
    if (this.authService.getToken()) {
      this.startPolling();
    }
  }

  startPolling() {
    this.fetchJobs();
    setInterval(() => this.fetchJobs(), 5000);
  }

  onFileSelected(event: any) {
    const file: File = event.target.files[0];
    if (file) {
      this.selectedFile = file;
    }
  }

  get token(): string | null {
    return this.authService.getToken();
  }

  private getAuthHeaders(): HttpHeaders {
    return new HttpHeaders({ 'Authorization': `Bearer ${this.token}` });
  }

  upload() {
    if (!this.selectedFile || !this.token) return;
    const headers = this.getAuthHeaders();
    const formData = new FormData();
    formData.append('file', this.selectedFile);
    
    this.http.post<Job>(`${environment.apiUrl}/jobs/`, formData, { headers }).pipe(
      tap(() => {
        this.selectedFile = null;
        this.fetchJobs();
      }),
      catchError(err => {
        alert('Upload failed: ' + (err.error.detail || err.message));
        return of(null);
      })
    ).subscribe();
  }

  fetchJobs() {
    if (!this.token) return;
    const headers = this.getAuthHeaders();
    
    this.http.get<Job[]>(`${environment.apiUrl}/jobs/`, { headers }).pipe(
      tap(jobs => {
        this.jobs = jobs;
      }),
      catchError(err => {
        console.error('Fetch jobs error', err);
        if (err.status === 401) {
          this.logout();
        }
        return of([]);
      })
    ).subscribe();
  }

  login() {
    const body = new HttpParams()
      .set('username', this.username)
      .set('password', this.password);
      
    this.http.post<{ access_token: string, token_type: string }>(
      `${environment.apiUrl}/auth/token`, 
      body.toString(), 
      {
        headers: new HttpHeaders({ 'Content-Type': 'application/x-www-form-urlencoded' })
      }
    ).pipe(
      tap(resp => {
        this.authService.setToken(resp.access_token);
        this.startPolling();
      }),
      catchError(err => {
        alert('Login failed: ' + (err.error.detail || err.message));
        return of(null);
      })
    ).subscribe();
  }

  register() {
    this.http.post<any>(
      `${environment.apiUrl}/auth/register`, 
      {
        username: this.username,
        password: this.password,
        email: this.email || undefined
      }
    ).pipe(
      tap(() => {
        alert('Registration successful. Please log in.');
        this.isRegisterMode = false;
      }),
      catchError(err => {
        alert('Registration failed: ' + (err.error.detail || err.message));
        return of(null);
      })
    ).subscribe();
  }

  toggleMode() {
    this.isRegisterMode = !this.isRegisterMode;
  }

  logout() {
    this.authService.setToken(null);
    this.jobs = [];
  }
}
