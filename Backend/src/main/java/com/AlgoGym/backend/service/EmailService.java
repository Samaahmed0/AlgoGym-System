package com.AlgoGym.backend.service;


import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import com.sendgrid.Method;
import com.sendgrid.Request;
import com.sendgrid.Response;
import com.sendgrid.SendGrid;

import com.sendgrid.helpers.mail.Mail;
import com.sendgrid.helpers.mail.objects.Content;
import com.sendgrid.helpers.mail.objects.Email;
import java.io.IOException;

@Service
@Slf4j
public class EmailService {

    @Value("${sendgrid.api-key}")
    private String sendGridApiKey;

    @Value("${sendgrid.from-email}")
    private String fromEmail;

    @Value("${sendgrid.from-name}")
    private String fromName;

    @Value("${app.frontend-url}")
    private String frontendUrl;

    /**
     * Sends a password reset email with an HTML template.
     *
     * @param toEmail   Recipient email address
     * @param token     The reset token (will be embedded in the link)
     */
    public void sendPasswordResetEmail(String toEmail, String token) {
        String resetLink = frontendUrl + "/reset-password?token=" + token;

        Email from = new Email(fromEmail, fromName);
        Email to = new Email(toEmail);
        String subject = "Reset Your AlgoGym Password";

        Content htmlContent = new Content("text/html", buildResetEmailHtml(resetLink));

        Mail mail = new Mail(from, subject, to, htmlContent);

        SendGrid sg = new SendGrid(sendGridApiKey);
        Request request = new Request();

        try {
            request.setMethod(Method.POST);
            request.setEndpoint("mail/send");
            request.setBody(mail.build());
            Response response = sg.api(request);

            if (response.getStatusCode() >= 400) {
                // Log the error but don't expose details to the user
                log.error("SendGrid error: status={}, body={}",
                        response.getStatusCode(), response.getBody());
                throw new RuntimeException("Failed to send email");
            }

            log.info("Password reset email sent to {}", toEmail);

        } catch (IOException e) {
            log.error("IOException sending email to {}: {}", toEmail, e.getMessage());
            throw new RuntimeException("Failed to send email", e);
        }
    }

    /**
     * Builds a clean HTML email template.
     * Inline styles are used because many email clients strip <style> tags.
     */
    private String buildResetEmailHtml(String resetLink) {
        return """
            <!DOCTYPE html>
            <html>
            <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
                <div style="max-width: 500px; margin: 0 auto; background: white;
                            border-radius: 8px; padding: 32px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    
                    <h1 style="color: #1a1a2e; font-size: 24px; margin-bottom: 8px;">
                        🏋️ AlgoGym
                    </h1>
                    <h2 style="color: #333; font-size: 18px; font-weight: normal;">
                        Reset Your Password
                    </h2>
                    
                    <p style="color: #555; line-height: 1.6;">
                        We received a request to reset your password. 
                        Click the button below to choose a new one.
                    </p>
                    
                    <a href="%s"
                       style="display: inline-block; background-color: #6c63ff; color: white;
                              padding: 12px 28px; border-radius: 6px; text-decoration: none;
                              font-weight: bold; margin: 20px 0;">
                        Reset Password
                    </a>
                    
                    <p style="color: #888; font-size: 13px;">
                        This link expires in <strong>1 hour</strong>. 
                        If you didn't request a password reset, you can safely ignore this email.
                    </p>
                    
                    <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                    <p style="color: #aaa; font-size: 12px;">
                        AlgoGym — AI-Powered Coding Practice
                    </p>
                </div>
            </body>
            </html>
            """.formatted(resetLink);
    }
}